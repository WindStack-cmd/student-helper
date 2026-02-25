// Contact Form
document.querySelector(".contact-form form").addEventListener("submit", function(e) {
    e.preventDefault();

    alert("Message sent successfully! We will get back to you soon.");

    this.reset();
});

// Review Form
document.querySelector(".review-section form").addEventListener("submit", function(e) {
    e.preventDefault();

    alert("Thank you for your feedback!");

    this.reset();
});
