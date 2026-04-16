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
    const bountyInput = document.getElementById("requestBounty");
    const bounty = parseInt(bountyInput.value || 0);
    const currentEmail = typeof getCurrentUserEmail === "function" ? getCurrentUserEmail() : "";

    // Get auth headers
    const headers = getAuthHeaders();
    if (!headers) {
        btn.innerHTML = originalText;
        btn.disabled = false;
        return;
    }

    try {
        // First validate balance
        const balanceUrl = currentEmail
            ? `http://127.0.0.1:5001/get_balance?email=${encodeURIComponent(currentEmail)}`
            : "http://127.0.0.1:5001/get_balance";
        const balanceRes = await fetch(balanceUrl);
        if (balanceRes.status === 401) {
            alert("Your session has expired. Please sign in again.");
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }
        if (!balanceRes.ok) throw new Error("Failed to verify balance");
        const balanceData = await balanceRes.json();
        
        if (bounty > balanceData.balance) {
            alert(`Insufficient balance! Your current balance is ${balanceData.balance} PTS.`);
            btn.innerHTML = originalText;
            btn.disabled = false;
            return;
        }

        const response = await fetch("http://127.0.0.1:5001/post_request", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
                title: title,
                description: description,
                email: currentEmail,
                bounty: bounty,
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
            const errMsg = errData.message || ("HTTP " + response.status);
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
    
    // Fetch and display balance for the current user
    async function updateStatusBalance() {
        const headers = getAuthHeaders();
        if (!headers) return;
        try {
            const currentEmail = typeof getCurrentUserEmail === "function" ? getCurrentUserEmail() : "";
            const balanceUrl = currentEmail
                ? `http://127.0.0.1:5001/get_balance?email=${encodeURIComponent(currentEmail)}`
                : "http://127.0.0.1:5001/get_balance";
            const res = await fetch(balanceUrl);
            if (res.ok) {
                const data = await res.json();
                const display = document.getElementById("balanceDisplay");
                if (display) display.textContent = `CURRENT_BALANCE: ${data.balance} PTS`;
            }
        } catch (e) {}
    }
    updateStatusBalance();
});