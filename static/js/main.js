/**
 * VerzendConnect - Main JavaScript
 */

// CSRF Token for AJAX requests
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return null;
}

// Configure fetch defaults
const fetchWithCSRF = (url, options = {}) => {
    return fetch(url, {
        ...options,
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
            ...options.headers,
        },
    });
};

// Cart functionality
const Cart = {
    async add(productId, quantity = 1) {
        try {
            const response = await fetchWithCSRF('/cart/add/', {
                method: 'POST',
                body: JSON.stringify({ product_id: productId, quantity }),
            });
            const data = await response.json();
            if (data.success) {
                this.updateCartCount(data.cart_count);
                this.showNotification('Product added to cart!', 'success');
            } else {
                this.showNotification(data.error || 'Failed to add product', 'error');
            }
            return data;
        } catch (error) {
            console.error('Add to cart error:', error);
            this.showNotification('Something went wrong', 'error');
        }
    },

    async update(productId, quantity) {
        try {
            const response = await fetchWithCSRF('/cart/update/', {
                method: 'POST',
                body: JSON.stringify({ product_id: productId, quantity }),
            });
            const data = await response.json();
            if (data.success) {
                this.updateCartCount(data.cart_count);
                this.updateCartTotal(data.cart_total);
            }
            return data;
        } catch (error) {
            console.error('Update cart error:', error);
        }
    },

    async remove(productId) {
        try {
            const response = await fetchWithCSRF('/cart/remove/', {
                method: 'POST',
                body: JSON.stringify({ product_id: productId }),
            });
            const data = await response.json();
            if (data.success) {
                this.updateCartCount(data.cart_count);
                this.showNotification('Product removed from cart', 'success');
            }
            return data;
        } catch (error) {
            console.error('Remove from cart error:', error);
        }
    },

    updateCartCount(count) {
        const cartCountElements = document.querySelectorAll('.cart-count');
        cartCountElements.forEach(el => {
            el.textContent = count;
            el.classList.toggle('hidden', count === 0);
        });
    },

    updateCartTotal(total) {
        const cartTotalElements = document.querySelectorAll('.cart-total');
        cartTotalElements.forEach(el => {
            el.textContent = `€${total.toFixed(2)}`;
        });
    },

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `fixed bottom-4 right-4 z-50 p-4 rounded-xl shadow-lg animate-slide-up ${
            type === 'success' ? 'bg-success-500 text-white' : 
            type === 'error' ? 'bg-error-500 text-white' : 
            'bg-secondary-800 text-white'
        }`;
        notification.innerHTML = `
            <div class="flex items-center gap-3">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="text-white/80 hover:text-white">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('opacity-0', 'transition-opacity', 'duration-300');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
};

// Dropdown functionality
const Dropdowns = {
    init() {
        document.addEventListener('click', (e) => {
            const toggle = e.target.closest('[data-dropdown-toggle]');
            if (toggle) {
                e.preventDefault();
                const targetId = toggle.dataset.dropdownToggle;
                const dropdown = document.getElementById(targetId);
                if (dropdown) {
                    dropdown.classList.toggle('hidden');
                }
            } else {
                // Close all dropdowns when clicking outside
                document.querySelectorAll('[data-dropdown]').forEach(dropdown => {
                    if (!dropdown.contains(e.target)) {
                        dropdown.classList.add('hidden');
                    }
                });
            }
        });
    }
};

// Mobile menu
const MobileMenu = {
    init() {
        const toggle = document.getElementById('mobile-menu-toggle');
        const menu = document.getElementById('mobile-menu');
        
        if (toggle && menu) {
            toggle.addEventListener('click', () => {
                menu.classList.toggle('hidden');
            });
        }
    }
};

// Search functionality
const Search = {
    init() {
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        let debounceTimeout;

        if (searchInput && searchResults) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimeout);
                const query = e.target.value.trim();
                
                if (query.length < 2) {
                    searchResults.classList.add('hidden');
                    return;
                }

                debounceTimeout = setTimeout(async () => {
                    try {
                        const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`);
                        const data = await response.json();
                        this.renderResults(data.results, searchResults);
                    } catch (error) {
                        console.error('Search error:', error);
                    }
                }, 300);
            });

            // Close search results when clicking outside
            document.addEventListener('click', (e) => {
                if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                    searchResults.classList.add('hidden');
                }
            });
        }
    },

    renderResults(results, container) {
        if (results.length === 0) {
            container.innerHTML = '<p class="p-4 text-secondary-500">No products found</p>';
        } else {
            container.innerHTML = results.map(product => {
                const placeholderUrl = '/static/images/placeholder.svg';
                const imageUrl = product.image || placeholderUrl;
                return `
                    <a href="${product.url}" class="dropdown-item flex items-center gap-3">
                        <div class="w-12 h-12 flex-shrink-0 rounded-lg overflow-hidden bg-secondary-100 flex items-center justify-center">
                            <img src="${imageUrl}" 
                                 alt="${product.name}" 
                                 class="w-full h-full object-cover"
                                 onerror="this.onerror=null; this.src='${placeholderUrl}'; this.classList.add('p-2')">
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="font-medium text-secondary-800 truncate">${product.name}</p>
                            <p class="text-sm text-primary-600">€${product.price}</p>
                        </div>
                    </a>
                `;
            }).join('');
        }
        container.classList.remove('hidden');
    }
};

// Quantity selector
const QuantitySelector = {
    init() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-quantity-btn]');
            if (!btn) return;

            const wrapper = btn.closest('[data-quantity-wrapper]');
            const input = wrapper.querySelector('input[type="number"]');
            const action = btn.dataset.quantityBtn;
            const productId = wrapper.dataset.productId;
            
            let value = parseInt(input.value) || 1;
            
            if (action === 'increase') {
                value = Math.min(value + 1, parseInt(input.max) || 99);
            } else if (action === 'decrease') {
                value = Math.max(value - 1, parseInt(input.min) || 1);
            }
            
            input.value = value;
            
            // If on cart page, update cart
            if (productId) {
                Cart.update(productId, value);
            }
        });
    }
};

// Image gallery
const ImageGallery = {
    init() {
        const thumbnails = document.querySelectorAll('[data-thumbnail]');
        const mainImage = document.getElementById('main-product-image');
        
        if (thumbnails.length && mainImage) {
            thumbnails.forEach(thumb => {
                thumb.addEventListener('click', () => {
                    mainImage.src = thumb.dataset.thumbnail;
                    thumbnails.forEach(t => t.classList.remove('ring-2', 'ring-primary-500'));
                    thumb.classList.add('ring-2', 'ring-primary-500');
                });
            });
        }
    }
};

// Initialize all modules
document.addEventListener('DOMContentLoaded', () => {
    Dropdowns.init();
    MobileMenu.init();
    Search.init();
    QuantitySelector.init();
    ImageGallery.init();
});

// Expose Cart globally for inline handlers
window.Cart = Cart;

