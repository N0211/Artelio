// Basic JavaScript for interactivity

// Image gallery lightbox effect
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('.artwork-item img');
    images.forEach(img => {
        img.addEventListener('click', function() {
            // Simple lightbox implementation
            const lightbox = document.createElement('div');
            lightbox.style.position = 'fixed';
            lightbox.style.top = '0';
            lightbox.style.left = '0';
            lightbox.style.width = '100%';
            lightbox.style.height = '100%';
            lightbox.style.backgroundColor = 'rgba(0,0,0,0.8)';
            lightbox.style.display = 'flex';
            lightbox.style.justifyContent = 'center';
            lightbox.style.alignItems = 'center';
            lightbox.style.zIndex = '1000';

            const imgClone = img.cloneNode();
            imgClone.style.maxWidth = '90%';
            imgClone.style.maxHeight = '90%';
            lightbox.appendChild(imgClone);

            lightbox.addEventListener('click', function() {
                document.body.removeChild(lightbox);
            });

            document.body.appendChild(lightbox);
        });
    });
});

// Form validation
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    form.addEventListener('submit', function(e) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.style.borderColor = 'red';
            } else {
                field.style.borderColor = '#ddd';
            }
        });

        if (!isValid) {
            e.preventDefault();
            alert('Please fill in all required fields.');
        }
    });
});
