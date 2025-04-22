
document.addEventListener("DOMContentLoaded", function () {
    let chatContainer = document.getElementById("chat-container");
    let botVideo = document.getElementById("botVideo");
    let sendBtn = document.getElementById("send-btn");
    let userInputField = document.getElementById("user-input");
    let chatBox = document.getElementById("chat-box");

    function restartVideo() {
        if (botVideo) {
            botVideo.currentTime = 0; // Restart video
            botVideo.play(); // Ensure it plays
        }
    }

    // ✅ Toggle chat on video click
    if (botVideo && chatContainer) {
        botVideo.addEventListener("click", function () {
            chatContainer.classList.toggle("hidden"); // Open/close chatbox
        });
    }

    // ✅ Restart video when user sends a message
    function handleMessageEvent() {
        sendMessage();
        restartVideo();
    }

    if (userInputField) {
        userInputField.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                handleMessageEvent();
            }
        });
    }

    if (sendBtn) {
        sendBtn.addEventListener("click", handleMessageEvent);
    }

    // ✅ Function to send user message
    function sendMessage() {
        let userInput = userInputField.value.trim();
        if (userInput === "") return; // Prevent empty messages

        let userMessage = document.createElement("div");
        userMessage.classList.add("message", "user");
        userMessage.innerHTML = `<span class="avatar">🧑</span><div class="text">${userInput}</div>`;
        chatBox.appendChild(userMessage);

        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to latest message
        userInputField.value = ""; // Clear input field

        showTalkingAnimation(); // Start animation

        fetch("/chatbot-response/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCSRFToken()
            },
            body: new URLSearchParams({ "message": userInput })
        })
        .then(response => response.json())
        .then(data => {
    let botMessage = document.createElement("div");
    botMessage.classList.add("message", "bot");
    botMessage.innerHTML = `<span class="avatar">🤖</span><div class="text">${formatResponse(data.response)}</div>`;
    chatBox.appendChild(botMessage);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll

    // ✅ Play audio if available
    if (data.audio_url) {
        console.log("Playing audio from:", data.audio_url);
        const audio = new Audio(data.audio_url);
        audio.play().catch(err => {
            console.error("Audio playback failed:", err);
        });
    }

    hideTalkingAnimation(); // Stop animation
    adjustVideoSize(); // Adjust video size
})

        .catch(error => {
            console.error("Error:", error);
            hideTalkingAnimation();
        });
    }

    // ✅ Function to adjust video size dynamically
    function adjustVideoSize() {
        let chatMessages = chatBox.children.length;
        if (botVideo) {
            if (chatMessages > 5) {
                botVideo.style.width = "30%"; // Reduce size when messages increase
            } else {
                botVideo.style.width = "50%"; // Default size
            }
        }
    }

    function showTalkingAnimation() {
        let animationElement = document.querySelector('.talking-animation');
        if (animationElement) {
            animationElement.style.opacity = '1';
        }
    }

    function hideTalkingAnimation() {
        let animationElement = document.querySelector('.talking-animation');
        if (animationElement) {
            animationElement.style.opacity = '0';
        }
    }

    function formatResponse(response) {
        return response.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                       .replace(/\*(.*?)\*/g, "<em>$1</em>")
                       .replace(/```([\s\S]*?)```/g, "<pre>$1</pre>")
                       .replace(/`(.*?)`/g, "<code>$1</code>")
                       .replace(/\n/g, "<br>")
                       .replace(/\* (.*?)<br>/g, "• $1<br>");
    }

    function getCSRFToken() {
        let cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith("csrftoken=")) {
                return cookie.substring("csrftoken=".length);
            }
        }
        return "";
    }
    
});
let recordBtn = document.getElementById("record-btn");
let responseAudio = document.getElementById("response-audio");
let mediaRecorder;
let audioChunks = [];

recordBtn.addEventListener("click", async () => {
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
        try {
            audioChunks = [];
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    audioChunks.push(e.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' }); // Correct MIME
                const formData = new FormData();
                formData.append("audio_file", audioBlob, "user_audio.webm"); // Correct extension

                try {
                    const response = await fetch("/speech-to-speech/", {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": getCSRFToken() // 💡 Ensure CSRF is sent if needed by Django
                        },
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error(`Server responded with ${response.status}`);
                    }

                    const result = await response.json();

                    // Add user message placeholder
                    let userText = document.createElement("div");
                    userText.classList.add("message", "user");
                    userText.innerHTML = `<span class="avatar">🧑</span><div class="text"><em>[Voice Message]</em></div>`;
                    chatBox.appendChild(userText);

                    // Bot response
                    let botText = document.createElement("div");
                    botText.classList.add("message", "bot");
                    botText.innerHTML = `<span class="avatar">🤖</span><div class="text">${result.response}</div>`;
                    chatBox.appendChild(botText);
                    chatBox.scrollTop = chatBox.scrollHeight;

                    // Play audio response
                    if (result.audio_url) {
                        responseAudio.src = result.audio_url;
                        responseAudio.hidden = false;
                        responseAudio.play();
                    }
                } catch (error) {
                    console.error("Error processing speech-to-speech:", error);
                    let errMsg = document.createElement("div");
                    errMsg.classList.add("message", "bot");
                    errMsg.innerHTML = `<span class="avatar">🤖</span><div class="text"><em>Error processing voice input.</em></div>`;
                    chatBox.appendChild(errMsg);
                }
            };

            mediaRecorder.start();
            recordBtn.textContent = "🛑 Stop";
        } catch (err) {
            console.error("Microphone access denied or other error:", err);
        }
    } else {
        mediaRecorder.stop();
        recordBtn.textContent = "🎤 Speak";
    }
});
