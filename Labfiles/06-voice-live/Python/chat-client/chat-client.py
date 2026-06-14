import os
import asyncio
import base64
import queue
from dotenv import load_dotenv
import pyaudio
from azure.identity.aio import DefaultAzureCredential
from azure.ai.voicelive.aio import connect
from azure.ai.voicelive.models import (
    InputAudioFormat,
    Modality,
    OutputAudioFormat,
    RequestSession,
    ServerEventType,
    AudioNoiseReduction,
    AudioEchoCancellation,
    AzureSemanticVadMultilingual,
    AgentConfig
) 


def main():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        load_dotenv()
        endpoint = os.environ.get("AZURE_VOICELIVE_ENDPOINT")
        agent_name = os.environ.get("AZURE_VOICELIVE_AGENT_ID")
        project_name = os.environ.get("AZURE_VOICELIVE_PROJECT_NAME")
        agent_config = AgentConfig({ "agent_name": agent_name, "project_name": project_name })
        credential = DefaultAzureCredential()
        assistant = VoiceAssistant(
            endpoint=endpoint,
            credential=credential,
            agent_config=agent_config
        )
        
        try:
            asyncio.run(assistant.start())
        except KeyboardInterrupt:
            print("\nGoodbye!")
    except Exception as e:
        print(f"An error occurred: {e}")

class VoiceAssistant:
    """
    Main voice assistant that coordinates the conversation flow.
    
    This class demonstrates the essential pattern for Azure VoiceLive:
    1. Connect to the service
    2. Configure the session
    3. Start audio capture/playback
    4. Process events from the service
    """
    
    def __init__(self, endpoint, credential, agent_config):
        self.endpoint = endpoint
        self.credential = credential
        self.agent_config = agent_config
    
    async def start(self):
        print("\n" + "=" * 60)
        print(f"{self.agent_config['agent_name']}")
        print("=" * 60)

        try:
            print("[DEBUG] Connecting to Azure VoiceLive...")
            async with connect(
                endpoint=self.endpoint,
                credential=self.credential,
                api_version="2026-01-01-preview",
                agent_config=self.agent_config
            ) as connection:
                print("[DEBUG] Connected!")
                print("[DEBUG] Connection object:", connection)
                print("[DEBUG] Connection type:", type(connection))
                self.connection = connection
                    
                self.audio_processor = AudioProcessor(connection)
                print("[DEBUG] AudioProcessor created")
                                  
                # STEP 3: Configure the session
                await self.setup_session()
                print("[DEBUG] Session configured")
                
                # STEP 4: Start audio systems
                self.audio_processor.start_playback()
                print("[DEBUG] Playback started")
                self.audio_processor.start_capture()
                print("[DEBUG] Capture started immediately (not waiting for SESSION_UPDATED)")
        
                print("\nReady! Start speaking...")
                print("Press Ctrl+C to exit\n")
                
                # STEP 5: Process events - this should block indefinitely
                print("[DEBUG] Starting event loop...")
                await self.process_events()
                print("[DEBUG] Event loop exited")

        except Exception as e:
            print(f"[ERROR] Exception in start(): {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("[DEBUG] Shutting down...")
            if hasattr(self, 'audio_processor'):
                self.audio_processor.shutdown()
    
    async def setup_session(self):
        """Configure the session with audio settings."""
        
        session_config = RequestSession(
            # Enable both text and audio
            modalities=[Modality.TEXT, Modality.AUDIO],
            
            # Audio format (16-bit PCM at 24kHz)
            input_audio_format=InputAudioFormat.PCM16,
            output_audio_format=OutputAudioFormat.PCM16,
            
            # Voice activity detection (when to detect speech)
            turn_detection=AzureSemanticVadMultilingual(),
            
            # Prevent echo from speaker feedback
            input_audio_echo_cancellation=AudioEchoCancellation(),
            
            # Reduce background noise
            input_audio_noise_reduction=AudioNoiseReduction(type="azure_deep_noise_suppression")
        )
        
        await self.connection.session.update(session=session_config)
    
    async def process_events(self):
        """Continuously listen for events from the service."""
        try:
            print("[DEBUG] Connection object:", self.connection)
            print("[DEBUG] Checking connection attributes...")
            print("[DEBUG] Dir of connection:", [attr for attr in dir(self.connection) if not attr.startswith('_')])
            
            # Try to get the underlying iterator/async generator
            print("[DEBUG] About to iterate over connection...")
            
            # Check if we need to call a method to get events
            event_stream = None
            if hasattr(self.connection, '__aiter__'):
                print("[DEBUG] Connection has __aiter__ method")
                event_stream = self.connection
            elif hasattr(self.connection, 'messages'):
                print("[DEBUG] Connection has 'messages' method, using that")
                event_stream = self.connection.messages()
            else:
                print("[DEBUG] No __aiter__ or messages method found")
                event_stream = self.connection
            
            # Listen for events from the service
            event_count = 0
            print("[DEBUG] About to start async for loop...")
            async for event in event_stream:
                event_count += 1
                print(f"[EVENT {event_count}] Received event")
                print(f"[DEBUG] Event object: {event}")
                print(f"[DEBUG] Event type: {type(event)}")
                try:
                    await self.handle_event(event)
                except Exception as e:
                    print(f"Error handling event: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue processing other events
            print(f"[INFO] Event loop ended after {event_count} events")
        except asyncio.CancelledError:
            print("Event processing cancelled")
        except StopAsyncIteration:
            print("[INFO] Event iterator ended (StopAsyncIteration)")
        except Exception as e:
            print(f"[ERROR] Connection error: {e}")
            import traceback
            traceback.print_exc()
    
    async def handle_event(self, event):
        """Handle events from the service."""
        try:
            event_type = getattr(event, 'type', None)
            print(f"[DEBUG] Processing event type: {event_type}")
            
            # Session is ready - start capturing audio NOW
            if event_type == ServerEventType.SESSION_UPDATED:
                try:
                    agent_name = event.session.agent.name if hasattr(event, 'session') else 'Unknown'
                    print(f"Connected to agent: {agent_name}")
                    self.audio_processor.start_capture()
                    print("[DEBUG] Audio capture started after SESSION_UPDATED")
                except Exception as e:
                    print(f"Error starting capture: {e}")
                    import traceback
                    traceback.print_exc()
            
            elif event_type == ServerEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED:
                transcript = event.get("transcript", "") if hasattr(event, 'get') else ""
                if transcript:
                    print(f"You: {transcript}")
            
            # Agent is responding with audio transcript
            elif event_type == ServerEventType.RESPONSE_AUDIO_TRANSCRIPT_DONE:
                transcript = event.get("transcript", "") if hasattr(event, 'get') else ""
                if transcript:
                    print(f"Agent: {transcript}")
            
            # User started speaking (interrupt any playing audio)
            elif event_type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
                self.audio_processor.clear_playback_queue()
                print("Listening...")
            
            # User stopped speaking
            elif event_type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED:
                print("Thinking...")
            
            # Receiving audio response chunks
            elif event_type == ServerEventType.RESPONSE_AUDIO_DELTA:
                if hasattr(event, 'delta') and event.delta:
                    self.audio_processor.queue_audio(event.delta)
            
            elif event_type == ServerEventType.RESPONSE_AUDIO_DONE:
                print("Response complete\n")
            
            elif event_type == ServerEventType.ERROR:
                error_msg = event.error.message if hasattr(event, 'error') else str(event)
                print(f"Error from service: {error_msg}")
            
            else:
                print(f"[DEBUG] Unhandled event type: {event_type}")
                
        except Exception as e:
            print(f"[ERROR] Exception in handle_event: {e}")
            import traceback
            traceback.print_exc()


# AudioProcessor class - handles microphone input and speaker output using PyAudio
class AudioProcessor:
    """
    Handles audio input (microphone) and output (speakers).
    
    Key responsibilities:
    - Capture audio from microphone and send to VoiceLive
    - Receive audio from VoiceLive and play through speakers
    """
    
    def __init__(self, connection):
        self.connection = connection
        self.audio = pyaudio.PyAudio()
        
        # Audio settings: 24kHz, 16-bit PCM, mono
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 24000
        self.chunk_size = 1200  # 50ms chunks
        
        # Streams for input and output
        self.input_stream = None
        self.output_stream = None
        self.playback_queue = queue.Queue()
    
    def start_capture(self):
        # Store event loop for use in callback thread
        self.loop = asyncio.get_event_loop()
        
        def capture_callback(in_data, frame_count, time_info, status):
            # Convert audio to base64 and send to VoiceLive
            audio_base64 = base64.b64encode(in_data).decode("utf-8")
            asyncio.run_coroutine_threadsafe(
                self.connection.input_audio_buffer.append(audio=audio_base64),
                self.loop
            )
            return (None, pyaudio.paContinue)
        
        self.input_stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=capture_callback
        )
        print("Microphone started")
    
    def start_playback(self):        
        remaining = bytes()
        
        def playback_callback(in_data, frame_count, time_info, status):
            nonlocal remaining
            
            # Calculate bytes needed
            bytes_needed = frame_count * pyaudio.get_sample_size(pyaudio.paInt16)
            output = remaining[:bytes_needed]
            remaining = remaining[bytes_needed:]
            
            # Get more audio from queue if needed
            while len(output) < bytes_needed:
                try:
                    audio_data = self.playback_queue.get_nowait()
                    if audio_data is None:  # End signal
                        break
                    output += audio_data
                except queue.Empty:
                    # Pad with silence if no audio available
                    output += bytes(bytes_needed - len(output))
                    break
            
            # Keep any extra for next callback
            if len(output) > bytes_needed:
                remaining = output[bytes_needed:]
                output = output[:bytes_needed]
            
            return (output, pyaudio.paContinue)
        
        self.output_stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            output=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=playback_callback
        )
        print(" Speakers ready")
    
    def queue_audio(self, audio_data):
        # Add audio data to the playback queue.
        self.playback_queue.put(audio_data)
    
    def clear_playback_queue(self):
        while not self.playback_queue.empty():
            try:
                self.playback_queue.get_nowait()
            except queue.Empty:
                break
    
    def shutdown(self):
        """Clean up audio resources."""
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        
        if self.output_stream:
            self.playback_queue.put(None)  # Signal end
            self.output_stream.stop_stream()
            self.output_stream.close()
        
        self.audio.terminate()
        print("Audio stopped")
if __name__ == "__main__":
    main()