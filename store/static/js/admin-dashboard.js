// Profile overlay toggle
const profileBtn = document.getElementById('profileBtn')
const mobileProfileBtn = document.getElementById('mobileProfileBtn')
const profileOverlay = document.getElementById('profileOverlay')
const closeProfileBtn = document.getElementById('closeProfileBtn')

if (profileBtn) {
    profileBtn.addEventListener('click', () => {
        profileOverlay.classList.remove('hidden')
    })
}

if (mobileProfileBtn) {
    mobileProfileBtn.addEventListener('click', () => {
        profileOverlay.classList.remove('hidden')
    })
}

closeProfileBtn.addEventListener('click', () => {
    profileOverlay.classList.add('hidden')
})

// Close overlay when clicking outside
profileOverlay.addEventListener('click', (e) => {
    if (e.target === profileOverlay) {
        profileOverlay.classList.add('hidden')
    }
})

// Mobile menu toggle
const mobileMenuBtn = document.getElementById('mobileMenuBtn')
const closeMobileMenuBtn = document.getElementById('closeMobileMenuBtn')
const mobileMenu = document.querySelector('.mobile-menu')

if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => {
        mobileMenu.classList.add('open')
    })
}

if (closeMobileMenuBtn) {
    closeMobileMenuBtn.addEventListener('click', () => {
        mobileMenu.classList.remove('open')
    })
}

// Mobile tabs navigation
const ordersTabBtn = document.getElementById('ordersTabBtn')
const stockTabBtn = document.getElementById('stockTabBtn')
const announcementsTabBtn = document.getElementById('announcementsTabBtn')

const ordersTab = document.getElementById('ordersTab')
const stockTab = document.getElementById('stockTab')
const announcementsTab = document.getElementById('announcementsTab')

function activateTab(activeTab, activeBtn) {
    // Hide all tabs
    ;[ordersTab, stockTab, announcementsTab].forEach((tab) => {
        if (tab) tab.classList.add('hidden')
    })

        // Reset all buttons
        ;[ordersTabBtn, stockTabBtn, announcementsTabBtn].forEach((btn) => {
            if (btn) btn.classList.remove('bg-blue-600', 'bg-opacity-20', 'text-blue-400')
            if (btn) btn.classList.add('bg-navy-light', 'text-gray-300')
        })

    // Show active tab and set active button
    if (activeTab) activeTab.classList.remove('hidden')
    if (activeBtn) {
        activeBtn.classList.remove('bg-navy-light', 'text-gray-300')
        activeBtn.classList.add('bg-blue-600', 'bg-opacity-20', 'text-blue-400')
    }
}

if (ordersTabBtn) {
    ordersTabBtn.addEventListener('click', () => {
        activateTab(ordersTab, ordersTabBtn)
    })
}

if (stockTabBtn) {
    stockTabBtn.addEventListener('click', () => {
        activateTab(stockTab, stockTabBtn)
    })
}

if (announcementsTabBtn) {
    announcementsTabBtn.addEventListener('click', () => {
        activateTab(announcementsTab, announcementsTabBtn)
    })
}

// Initialize tabs
if (window.innerWidth < 768) {
    activateTab(ordersTab, ordersTabBtn)
}

// Restock modal: attach click events to all restock buttons
document.querySelectorAll('.restock-btn').forEach(function (button) {
    button.addEventListener('click', function () {
        const productId = this.getAttribute('data-product-id');
        const productName = this.getAttribute('data-product-name');
        document.getElementById('restockProductId').value = productId;
        document.getElementById('restockModalTitle').innerText = 'Restock ' + productName;
        document.getElementById('restockModal').classList.remove('hidden');
    });
});

// Cancel button closes the modal
document.getElementById('cancelRestockBtn').addEventListener('click', function () {
    document.getElementById('restockModal').classList.add('hidden');
});