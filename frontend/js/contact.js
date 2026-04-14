// Contact Form
const contactForm = document.querySelector(".contact-form form");
if (contactForm) {
    contactForm.addEventListener("submit", function(e) {
        e.preventDefault();

        alert("Message sent successfully! We will get back to you soon.");

        this.reset();
    });
}

// Review Form
const reviewForm = document.querySelector(".review-section form");
if (reviewForm) {
    reviewForm.addEventListener("submit", function(e) {
        e.preventDefault();

        alert("Thank you for your feedback!");

        this.reset();
    });
}
