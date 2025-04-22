from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
import os
import requests
import re
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from nltk.stem import WordNetLemmatizer
from pydub import AudioSegment
import uuid
import io
import time

# ✅ Load API Keys from .env

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")
VOICERSS_API_KEY = os.getenv("VOICERSS_API_KEY")
ASSEMBLY_API_KEY=os.getenv("ASSEMBLY_API_KEY")



# ✅ Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Define greeting & keyword categories
# Initialize Lemmatizer
lemmatizer = WordNetLemmatizer()

# Define expanded keyword categories
# 💬 Custom questions mapped to hardcoded responses
CUSTOM_RESPONSES = {
    
    "who are you": "I am MASSS – your friendly AI-powered career guidance assistant. I'm here to help you explore career paths, build strong resumes, and support your mental well-being. Just think of me as your personal mentor – but digital ✨",

    "introduce yourself": "Hello! I'm MASSS – an AI chatbot developed with love and purpose by an amazing team of students from Adamas University. My role is to guide, support, and empower you in your personal and professional journey. 💼🧠",

    "who created you": "I was created as part of a Mini Project by a brilliant group of Computer Science students at Adamas University, led by Mrinal Sahoo. This team was mentored by the incredible Debashree Mitra, whose guidance brought me to life. 💡👩‍🏫",

    "mrinal": "Mrinal Sahoo is the visionary behind my creation. He took the lead in bringing me to life, guiding the team, and ensuring I could think, respond, and help users just like you. Hats off to the mastermind! 🧠💻",

    "soma": "Soma Chatterjee is one of my creators who brought empathy and creativity to my responses. Thanks to her, I understand how to support users mentally and emotionally, not just professionally. 🌸🧘‍♀️",

    "subhangkar": "Subhangkar Barui added depth and logic to how I respond. With a keen understanding of AI and tech, he made sure my brain (code) works smoothly and intelligently. 🚀🧠",

    "saikat": "Saikat Pal played a crucial role in developing and styling me. His technical skills helped shape how I look and function – clean, responsive, and reliable. Thank you, Saikat! 🛠️👨‍💻",

    "arindam": "Arindam Jana brought structure and stability to my foundation. From backend logic to making sure I’m always up and running, Arindam ensured I’m not just smart, but strong too. 🧱⚙️"
}



GREETINGS = [
    "hi", "hello", "hey", "howdy", "hola", "greetings", "sup", "what's up",
    "good morning", "good evening", "good afternoon", "gm", "ge", "morning",
    "yo", "hiya", "how’s it going", "how are you", "what’s good", "how have you been",
    "salutations", "wassup", "long time no see", "how do you do","hii","about","how","show"
]


CAREER_KEYWORDS = [
    "job", "career", "profession", "work", "occupation", "employment", "vacancy",
    "recruitment", "hiring", "jobs", "career path", "career growth", "opportunity",
    "job market", "corporate", "industry", "field", "sector", "business",
    "career change", "freelancing", "entrepreneurship", "internship", "training",
    "promotion", "salary negotiation", "career transition", "headhunting",
    "skills development", "career planning", "leadership", "management", "HR",
    "job security", "workforce", "job description", "networking", "career coaching","College"
    ,"Thankyou ","Salary","Subjects","Semester","bsc","btech","job","review","aiml","csf","cse","stream","innovation","name","you"
    "goal","describe","technology","future","books","say"
]


RESUME_KEYWORDS = [
    "resume", "cv", "cover letter", "portfolio", "bio", "curriculum vitae",
    "profile summary", "resume format", "job application", "applying", "apply",
    "cv writing", "professional summary", "experience", "qualifications",
    "achievements", "certifications", "career objectives", "skills", "references",
    "work history", "internship experience", "projects", "LinkedIn profile",
    "ATS-friendly resume", "resume builder", "resume review", "job interview",
    "personal statement", "employment history", "gap in resume", "resume templates"
]


MENTAL_HEALTH_KEYWORDS = [
    "stress", "burnout", "depression","help", "mental health", "anxiety", "pressure",
    "work-life balance", "overwhelmed", "fatigue", "exhausted", "therapy",
    "psychologist", "psychiatrist", "self-care", "meditation", "mindfulness",
    "counseling", "emotional support", "mental well-being", "loneliness",
    "panic attacks", "negative thoughts", "productivity anxiety", "toxic workplace",
    "relaxation techniques", "psychotherapy", "mental health day", "deep breathing",
    "coping mechanisms", "insomnia", "social anxiety", "bipolar disorder",
    "burnout recovery", "positivity", "mental resilience", "journaling","speak","answer"
    ]


# Combine all keywords into a set
ALL_KEYWORDS = set(GREETINGS + CAREER_KEYWORDS + RESUME_KEYWORDS + MENTAL_HEALTH_KEYWORDS)
# ------------------- 🏠 HOME PAGE -------------------

def home(request):
    return render(request, "home.html")

# ------------------- 💬 CHATBOT PAGE -------------------

@login_required
def chat(request):
    return render(request, "chat.html")

# ------------------- 🎤 SPEECH-TO-TEXT (STT) API -------------------
# ------------------- 🤖 CHATBOT RESPONSE API -------------------
@csrf_exempt
def is_relevant_message(message):
    """Check if message contains words matching the allowed topics using fuzzy matching."""
    words = message.lower().split()

    for word in words:
        lemma = lemmatizer.lemmatize(word)  # Normalize words
        for keyword in ALL_KEYWORDS:
            if fuzz.ratio(lemma, keyword) > 80:  # Fuzzy match threshold
                return True
    return False


def chatbot_response(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    message = request.POST.get("message", "").strip().lower()
    if not message:
        return JsonResponse({"error": "No message provided"}, status=400)

    # ✅ Custom answers first
    for keyword, custom_reply in CUSTOM_RESPONSES.items():
        if keyword in message:
            audio_path = generate_tts_audio(custom_reply)
            if audio_path:
                audio_url = request.build_absolute_uri(f"/{audio_path.replace('\\', '/')}")
            else:
                audio_url = None
            return JsonResponse({"response": custom_reply, "audio_url": audio_url})

    # ✅ Now check topic relevance
    if not is_relevant_message(message):
        return JsonResponse({"response": "Sorry, I can only discuss career, resume, and mental health topics."})

    # Gemini + TTS
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(message)
        bot_response = response.text if response and hasattr(response, "text") else "Sorry, I couldn't generate a response."

        audio_path = generate_tts_audio(bot_response)
        if audio_path:
            audio_url = request.build_absolute_uri(f"/{audio_path.replace('\\', '/')}")
        else:
            audio_url = None

        return JsonResponse({
            "response": bot_response,
            "audio_url": audio_url
        })
    except Exception as e:
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)


# Function to handle Speech-to-Text (STT) using AssemblyAI
def speech_to_text(audio_file_path):
    try:
        # Step 1: Upload the audio file to AssemblyAI
        with open(audio_file_path, "rb") as audio_file:
            upload_response = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"authorization": ASSEMBLY_API_KEY},
                data=audio_file
            )
        if upload_response.status_code != 200:
            print(f"AssemblyAI Upload Error: {upload_response.status_code} - {upload_response.text}")
            return None

        upload_url = upload_response.json().get("upload_url")

        # Step 2: Request transcription
        transcript_response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers={"authorization": ASSEMBLY_API_KEY, "content-type": "application/json"},
            json={"audio_url": upload_url}
        )

        if transcript_response.status_code != 200:
            print(f"AssemblyAI Transcription Request Error: {transcript_response.status_code} - {transcript_response.text}")
            return None

        transcript_id = transcript_response.json().get("id")
        transcript_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

        # Step 3: Poll until the transcript is ready
        while True:
            status_response = requests.get(
                transcript_url,
                headers={"authorization": ASSEMBLY_API_KEY}
            )
            status_data = status_response.json()

            if status_data["status"] == "completed":
                return status_data["text"]
            elif status_data["status"] == "error":
                print(f"AssemblyAI Transcription Error: {status_data['error']}")
                return None

            time.sleep(3)  # Wait before polling again

    except Exception as e:
        print(f"Error processing STT with AssemblyAI: {e}")
        return None

# Function to generate a chatbot response based on user speech
def generate_speech_response(text):
    # Process message to generate Gemini response
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(text)
        bot_response = response.text if response and hasattr(response, "text") else "Sorry, I couldn't generate a response."

        # Generate TTS audio file from Gemini's response
        audio_path = generate_tts_audio(bot_response)
        if audio_path:
            return bot_response, audio_path
        else:
            return bot_response, None
    except Exception as e:
        return "Error processing your request", None

# Function to handle Speech-to-Speech workflow
@csrf_exempt


# Function to convert audio to WAV format
def convert_audio(audio_file_path):
    try:
        audio = AudioSegment.from_file(audio_file_path)
        audio = audio.set_channels(1).set_frame_rate(16000)  # Standardize audio format
        new_audio_path = audio_file_path.replace(".mp3", "_converted.wav").replace(".wav", "_converted.wav")
        audio.export(new_audio_path, format="wav")
        return new_audio_path
    except Exception as e:
        print(f"Error converting audio: {e}")
        return None
@csrf_exempt
def speech_to_speech(request):
    if request.method == 'POST':
        if 'audio' not in request.FILES:
            return JsonResponse({'error': 'No audio file uploaded'}, status=400)

        audio = request.FILES['audio']
        audio_bytes = audio.read()

        try:
            # Convert to WAV using pydub (assumes webm input from browser)
            sound = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
            wav_io = io.BytesIO()
            sound.export(wav_io, format="wav")
            wav_io.seek(0)
        except Exception as e:
            print("Error converting audio:", e)
            return JsonResponse({"error": "Could not process audio"}, status=400)

        try:
            # Upload the file to AssemblyAI
            upload_response = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"authorization": os.getenv("ASSEMBLY_API_KEY")},
                data=wav_io
            )
            upload_url = upload_response.json().get("upload_url")

            # Start transcription
            transcript_response = requests.post(
                "https://api.assemblyai.com/v2/transcript",
                json={"audio_url": upload_url},
                headers={"authorization": os.getenv("ASSEMBLY_API_KEY")}
            )
            transcript_id = transcript_response.json().get("id")

            # Poll until the transcript is ready
            transcript_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
            while True:
                status_response = requests.get(transcript_url, headers={"authorization": os.getenv("ASSEMBLY_API_KEY")})
                status_data = status_response.json()
                if status_data["status"] == "completed":
                    transcript = status_data["text"]
                    break
                elif status_data["status"] == "error":
                    return JsonResponse({"error": status_data["error"]}, status=500)

            print("🗣️ Transcript:", transcript)

            # Use Gemini AI to generate response
            model = genai.GenerativeModel("gemini-2.0-flash")
            gemini_response = model.generate_content(transcript)
            bot_response = gemini_response.text if gemini_response and hasattr(gemini_response, "text") else "Sorry, I couldn't generate a response."

            # Convert bot response to speech
            audio_path = generate_tts_audio(bot_response)
            if audio_path:
                audio_url = request.build_absolute_uri(f"/{audio_path.replace('\\', '/')}")
            else:
                audio_url = None

            return JsonResponse({
                "transcript": transcript,
                "response": bot_response,
                "audio_url": audio_url
            })

        except Exception as e:
            print("AssemblyAI or Gemini error:", e)
            return JsonResponse({'error': 'Error processing with AssemblyAI or Gemini'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def generate_tts_audio(text):
    if not os.path.exists("media"):
        os.makedirs("media")

    # Clean the text for TTS by removing markdown formatting
    clean_text = text
    clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)
    clean_text = re.sub(r'\*(.*?)\*', r'\1', clean_text)
    clean_text = re.sub(r'```([\s\S]*?)```', r'\1', clean_text)
    clean_text = re.sub(r'`(.*?)`', r'\1', clean_text)
    clean_text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', clean_text)
    clean_text = re.sub(r'#{1,6}\s+(.*?)$', r'\1', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'- (.*?)$', r'\1', clean_text, flags=re.MULTILINE)

    print(f"Original text: {text[:50]}...")
    print(f"Cleaned text for TTS: {clean_text[:50]}...")

    # Voice RSS TTS Setup
    voice_rss_api_key = os.getenv("VOICERSS_API_KEY")
    if not voice_rss_api_key:
        print("Voice RSS API key is missing.")
        return None

    try:
        # Prepare parameters for the Voice RSS API request
        url = "https://api.voicerss.org/"
        params = {
            "key": voice_rss_api_key,
            "hl": "en-in",  # Language code (English - US)
            "src": clean_text,
            "r": "3",  # Rate (speed of speech)
            "c": "mp3",  # Audio format
            "f": "44khz_16bit_stereo",  # Audio quality
            "b64": "false"  # Base64 encoding for direct download
            
        }

        # Call Voice RSS API for TTS audio generation
        response = requests.get(url, params=params)

        if response.status_code == 200:
            # Save the audio data as an MP3 file
            filename = f"tts_audio_{uuid.uuid4().hex}.mp3"
            file_path = os.path.join("media", filename)

            # Save the response content (audio) directly to file
            with open(file_path, "wb") as f:
                f.write(response.content)

            print(f"Audio file created at: {file_path}")
            return f"media/{filename}"

        else:
            print("Voice RSS API Error:", response.text)
            return None

    except Exception as e:
        print("Voice RSS TTS Exception:", str(e))
        return None


# ✅ User Signup
def user_signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Choose another one.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered. Try logging in.")
            return redirect("signup")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        # ✅ Create and save the user
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()

        messages.success(request, "Signup successful! You can now log in.")
        return redirect("login")

    return render(request, "signup.html")

# ✅ User Login
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "login.html")

# ✅ User Logout
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("login")

DID_API_KEY = "bXJpbmFsc2Fob28yNUBnbWFpbC5jb20:HcxwFO6ED6piNQ3AD20O5"  # Replace with your D-ID API key

def generate_avatar_response(text):
    url = "https://api.d-id.com/talks"
    
    payload = {
        "source_url": "https://example.com/avatar.png",  # Your avatar image
        "script": {
            "type": "text",
            "input": text
        }
    }
    
    headers = {
        "Authorization": f"Bearer {DID_API_KEY}",
        "Content-Type": "application/json"
    }

       
    response = requests.post(url, json=payload, headers=headers)
    return response.json()