from django.urls import path
from .views import chat, chatbot_response, user_login, user_logout, user_signup, home,speech_to_speech

urlpatterns = [
    path("", home, name="home"),
    path("chat/", chat, name="chat"),
    path("chatbot-response/", chatbot_response, name="chatbot_response"),
    
    # Authentication
    path("signup/", user_signup, name="signup"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path('speech-to-speech/', speech_to_speech, name='speech_to_speech'),
    
]
