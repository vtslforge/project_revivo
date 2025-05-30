// Main Dashboard Navigation

document.addEventListener('DOMContentLoaded', function() {
    // Ensure the page layout is initialized properly
    const dashboard = document.querySelector('.dashboard');
    if (dashboard) {
        dashboard.style.minHeight = 'calc(100vh - 800px)'; // Adjust based on background height
    }

    // Get all box elements
    const workoutBox = document.getElementById('workoutBox');
    const foodBox = document.getElementById('foodBox');
    const exploreBox = document.getElementById('exploreBox');
    const analyticsBox = document.getElementById('analyticsBox');

    // Add click events with animation
    [workoutBox, foodBox, exploreBox, analyticsBox].forEach(box => {
        box.addEventListener('click', function() {
            // Pulse animation on click
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);

            // Navigate to respective pages
            switch(this.id) {
                case 'workoutBox':
                    setTimeout(() => window.location.href = '/workout', 200);
                    break;
                case 'foodBox':
                    setTimeout(() => window.location.href = '/food', 200);
                    break;
                case 'exploreBox':
                    setTimeout(() => window.location.href = '/explore', 200);
                    break;
                case 'analyticsBox':
                    setTimeout(() => window.location.href = '/analytics', 200);
                    break;
            }
        });
    });

    // Add hover sound effect (optional)
    const boxes = document.querySelectorAll('.box');
    boxes.forEach(box => {
        box.addEventListener('mouseenter', () => {
            // Uncomment to add sound (requires audio file)
            // new Audio('/static/sounds/hover.mp3').play().catch(e => console.log("Sound disabled"));
        });
    });
});

// Back button functionality (for all subpages)
if(document.querySelector('.back-btn')) {
    document.querySelector('.back-btn').addEventListener('click', function() {
        this.style.transform = 'scale(0.95)';
        setTimeout(() => {
            window.location.href = '/';
        }, 150);
    });
}