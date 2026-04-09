// Help Request functionality

async function submitHelpRequest(event){
    if (event) event.preventDefault();

    const btn = document.getElementById("submitBtn");
    if (!btn) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = "Publishing...";
    btn.disabled = true;

    const title = document.getElementById("requestTitle").value.trim();
    const description = document.getElementById("requestDesc").value.trim();
    const type = document.getElementById("helpType").value;
    const category = document.getElementById("requestCategory").value;

    // Get email from localStorage (user data stored on login)
    let email = "";
    const userStr = localStorage.getItem("loggedInUser");
    if (userStr) {
        try {
            const user = JSON.parse(userStr);
            email = user.email || user.first_name || "";
        } catch(e) {
            console.error("Failed to parse loggedInUser:", e);
        }
    }

    if (!email) {
        alert("You must be logged in to post a request.");
        btn.innerHTML = originalText;
        btn.disabled = false;
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:5001/post_request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title: title,
                description: description,
                email: email,
                bounty: 50,
                category: category
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