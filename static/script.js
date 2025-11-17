// script.js - JavaScript enhancements for CondoRent app

document.addEventListener('DOMContentLoaded', function() {
    // Image preview for file uploads
    function setupImagePreview(inputId, previewId) {
        const input = document.getElementById(inputId);
        const preview = document.getElementById(previewId);
        if (input && preview) {
            input.addEventListener('change', function(event) {
                const file = event.target.files[0];
                if (file && file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                } else {
                    preview.style.display = 'none';
                }
            });
        }
    }

    // Setup previews for add and edit forms
    setupImagePreview('image-upload', 'image-preview');
    setupImagePreview('edit-image-upload', 'edit-image-preview');

    // Form validation
    function validateForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return true;

        let isValid = true;
        const inputs = form.querySelectorAll('input[required], select[required]');
        inputs.forEach(input => {
            if (!input.value.trim()) {
                showError(input, 'This field is required.');
                isValid = false;
            } else if (input.type === 'number' && input.value <= 0) {
                showError(input, 'Must be a positive number.');
                isValid = false;
            } else {
                clearError(input);
            }
        });
        return isValid;
    }

    function showError(input, message) {
        clearError(input);
        const error = document.createElement('div');
        error.className = 'error-message';
        error.textContent = message;
        input.parentNode.insertBefore(error, input.nextSibling);
        input.style.borderColor = '#FF385C';
    }

    function clearError(input) {
        const error = input.parentNode.querySelector('.error-message');
        if (error) error.remove();
        input.style.borderColor = '#E0E0E0';
    }

    // Attach validation to forms
    const addForm = document.querySelector('form[action*="add_condo"]');
    const editForm = document.querySelector('form[action*="update_condo"]');
    const loginForm = document.querySelector('form[action*="login"]');

    if (addForm) addForm.addEventListener('submit', e => { if (!validateForm(addForm.id || 'add-form')) e.preventDefault(); });
    if (editForm) editForm.addEventListener('submit', e => { if (!validateForm(editForm.id || 'edit-form')) e.preventDefault(); });
    if (loginForm) loginForm.addEventListener('submit', e => { if (!validateForm(loginForm.id || 'login-form')) e.preventDefault(); });

    // Custom modal for confirmations
    function showModal(message, onConfirm) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <p>${message}</p>
                <button class="btn-confirm">Yes</button>
                <button class="btn-cancel">No</button>
            </div>
        `;
        document.body.appendChild(modal);

        modal.querySelector('.btn-confirm').addEventListener('click', () => {
            onConfirm();
            modal.remove();
        });
        modal.querySelector('.btn-cancel').addEventListener('click', () => modal.remove());
    }

    // Replace confirm() with modal
    document.querySelectorAll('a[onclick*="confirm"]').forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            showModal('Are you sure you want to delete this condo?', () => window.location.href = link.href);
        });
    });

    // Smooth animations for cards
    const cards = document.querySelectorAll('.condo-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s, transform 0.5s';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Lazy loading for images
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });
    images.forEach(img => imageObserver.observe(img));

    // Back to top button
    const backToTop = document.createElement('button');
    backToTop.textContent = '↑';
    backToTop.className = 'back-to-top';
    backToTop.style.display = 'none';
    document.body.appendChild(backToTop);
    backToTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
    window.addEventListener('scroll', () => {
        backToTop.style.display = window.scrollY > 300 ? 'block' : 'none';
    });
});

// CSS for modal and other JS elements (add to style.css)
const style = document.createElement('style');
style.textContent = `
    .error-message { color: #FF385C; font-size: 12px; margin-top: 4px; }
    .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
    .modal { background: white; padding: 24px; border-radius: 12px; text-align: center; box-shadow: 0 4px 24px rgba(0,0,0,0.2); }
    .modal button { margin: 0 8px; padding: 8px 16px; border: none; border-radius: 8px; cursor: pointer; }
    .btn-confirm { background: #FF385C; color: white; }
    .btn-cancel { background: #F7F7F7; color: #222; }
    .back-to-top { position: fixed; bottom: 20px; right: 20px; background: #FF385C; color: white; border: none; border-radius: 50%; width: 50px; height: 50px; cursor: pointer; font-size: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.2); }
    .lazy { opacity: 0; transition: opacity 0.3s; }
    .lazy.loaded { opacity: 1; }
`;
document.head.appendChild(style);