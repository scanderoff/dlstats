"use strict";


const cityChoices = new Choices('[name="cities"]', {
    removeItemButton: true,
});

const restaurantChoices = new Choices('[name="restaurants"]', {
    removeItemButton: true,
});


(function () {
    const $productList = document.querySelector(".products__list");
    const $spinner = document.querySelector(".products__loader");
    let page = 1;

    const observer = new IntersectionObserver(onIntersect, {
        root: null,
        rootMargin: "0px",
        threshold: 0.0,
    });

    observer.observe($spinner);

    function onIntersect(entries, observer) {
        const entry = entries[0];

        if (!entry.isIntersecting) {
            return;
        }

        getProducts(++page);
    }

    function getProducts(page) {
        const url = new URL(location);
        url.searchParams.append("page", page);

        fetch(url, {
            method: "GET",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            }
        })
            .then(response => response.text())
            .then(onResponse)
        ;
    }

    function onResponse(html) {
        if (!html) {
            observer.unobserve($spinner);
            $spinner.remove();
            
            return;
        }

        $productList.insertAdjacentHTML("beforeend", html);
    }
}());









(function () {
    const $resetBtn = document.querySelector('.filter-form__btn[type="reset"]');

    $resetBtn.addEventListener("click", (event) => {
        location.search = "";
    });
}());
