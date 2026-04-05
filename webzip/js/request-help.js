// Help Request functionality

async function submitHelpRequest(event){
    if (event) event.preventDefault();

    const headers = getAuthHeaders();
    if (!headers) return;

    const btn = document.getElementById("submitBtn");
    if (!btn) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = "Publishing...";
    btn.disabled = true;

    const title = document.getElementById("requestTitle").value.trim();
    const description = document.getElementById("requestDesc").value.trim();
    const type = document.getElementById("helpType").value;

    try {
        const response = await fetch("http://127.0.0.1:5000/post_request", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({ 
                title: title, 
                description: description, 
                type: type,
                bounty: 50 
            })
        });

        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            const errMsg = errData.error || errData.message || ("HTTP " + response.status);
            alert("Failed to post request: " + errMsg);
            btn.innerHTML = originalText;
            btn.disabled = false;
            return;
        }

        const data = await response.json();
        alert(data.message || "Request posted successfully!");
        window.location.href = "dashboard.html";

    } catch (error) {
        console.error("post_request fetch error:", error);
        alert("Network error — could not reach backend. Is the Flask server running?");
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

document.addEventListener("DOMContentLoaded", function(){
    const btn = document.getElementById("initRequestBtn");
    if(btn){
        btn.addEventListener("click", function(){
            console.log("INIT REQUEST clicked");
        });
    }

    const form = document.getElementById("requestForm");
    if (form) {
        form.addEventListener("submit", submitHelpRequest);
    }
});