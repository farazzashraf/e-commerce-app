document.addEventListener('DOMContentLoaded', function () {
    new Swiper('.category-swiper', {
        slidesPerView: 2,
        spaceBetween: 10,
        loop: true,
        centeredSlides: false,
        speed: 800,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
            pauseOnMouseEnter: true
        },
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
        breakpoints: {
            // When window width is >= 480px
            480: {
                slidesPerView: 3,
                spaceBetween: 15
            },
            // When window width is >= 768px
            768: {
                slidesPerView: 4,
                spaceBetween: 20
            },
            // When window width is >= 992px
            992: {
                slidesPerView: 6,
                spaceBetween: 25
            }
        }
    });

    // Make category items clickable
    document.querySelectorAll('.category-item').forEach(item => {
        item.addEventListener('click', function () {
            const category = this.querySelector('span').textContent;
            // Find the corresponding filter button and click it
            const filterButtons = document.querySelectorAll('.filter-button');
            filterButtons.forEach(button => {
                if (button.textContent.trim() === category ||
                    (category === 'Sale' && button.textContent.trim() === 'All Items')) {
                    button.click();
                }
            });
        });
    });
});