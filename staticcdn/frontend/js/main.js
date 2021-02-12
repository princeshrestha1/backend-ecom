//initialize animation

//initiate product slider
$(document).ready(function() {
    $(".product-slider").slick({
        dots: true,
        infinite: false,
        speed: 300,
        slidesToShow: 4,
        slidesToScroll: 4,
        responsive: [{
                breakpoint: 1024,
                settings: {
                    slidesToShow: 3,
                    slidesToScroll: 3,
                    infinite: true,
                    dots: true,
                },
            },
            {
                breakpoint: 600,
                settings: {
                    slidesToShow: 2,
                    slidesToScroll: 2,
                },
            },
            {
                breakpoint: 480,
                settings: {
                    slidesToShow: 1,
                    slidesToScroll: 1,
                },
            },
        ],
    });
    $(".blog-slider").slick({
        dots: true,
        infinite: false,
        speed: 300,
        slidesToShow: 3,
        slidesToScroll: 3,
        responsive: [{
                breakpoint: 1024,
                settings: {
                    slidesToShow: 2,
                    slidesToScroll: 2,
                    infinite: true,
                    dots: true,
                },
            },
            {
                breakpoint: 600,
                settings: {
                    slidesToShow: 1,
                    slidesToScroll: 1,
                },
            },
            {
                breakpoint: 480,
                settings: {
                    slidesToShow: 1,
                    slidesToScroll: 1,
                },
            },
        ],
    });

    $(".smooth-slider").slick({
        slidesToShow: 3,
        autoplay: true,
        autoplaySpeed: 0,
        variableWidth: true,
        speed: 6000,
        cssEase: "linear",
        infinite: true,
        focusOnSelect: false,
        pauseOnHover: false,
        responsive: [{
                breakpoint: 768,
                settings: {
                    arrows: false,
                    slidesToShow: 3,
                },
            },
            {
                breakpoint: 480,
                settings: {
                    arrows: false,
                    slidesToShow: 1,
                },
            },
        ],
    });
});

//change nav color
const shopNav = document.getElementById("shop-nav");
document.getElementById("link1").addEventListener(
    "mouseover",
    function() {
        shopNav.style.backgroundImage =
            "";
    },
    false
);
document.getElementById("link1").addEventListener(
    "mouseout",
    function() {
        shopNav.style.backgroundImage = "";
    },
    false
);

// document.getElementById("link2").addEventListener(
//     "mouseover",
//     function() {
//         shopNav.style.backgroundImage =
//             "";
//     },
//     false
// );
// document.getElementById("link2").addEventListener(
//     "mouseout",
//     function() {
//         shopNav.style.backgroundImage = "";
//     },
//     false
// );

// document.getElementById("link3").addEventListener(
//     "mouseover",
//     function() {
//         shopNav.style.backgroundImage =
//             "";
//     },
//     false
// );
// document.getElementById("link3").addEventListener(
//     "mouseout",
//     function() {
//         shopNav.style.backgroundImage = "";
//     },
//     false
// );

// document.getElementById("link4").addEventListener(
//     "mouseover",
//     function() {
//         shopNav.style.backgroundImage =
//             "";
//     },
//     false
// );
// document.getElementById("link5").addEventListener(
//     "mouseout",
//     function() {
//         shopNav.style.backgroundImage = "url(https://source.unsplash.com/ke-PACXFFS8/800x600)";
//     },
//     false
// );

//image 360 rotate

$(".btn-plus, .btn-minus").on("click", function(e) {
    const isNegative = $(e.target).closest(".btn-minus").is(".btn-minus");
    const input = $(e.target).closest(".input-group").find("input");
    if (input.is("input")) {
        input[0][isNegative ? "stepDown" : "stepUp"]();
    }
});

function checkSubscribe() {
    if (document.getElementById("subscribe").checked) {
        document.getElementById("subscribeMe").style.display = "block";
    } else document.getElementById("subscribeMe").style.display = "none";
}

window.onscroll = function() {
    var doc = document.documentElement;
    var top = (window.pageYOffset || doc.scrollTop) - (doc.clientTop || 0);
    if (top <= 700) {
        $("#image-sticky").css("position", "sticky");
        $("#image-sticky").css("top", "100px");
    } else {
        $("#image-sticky").css("position", "relative");
        $("#image-sticky").css("top", "640px");
    }
};

const detailsAlert = () => {
    swal(
        "Plant Protein Blend (Pea Protein; Organic Pumpkin (Cucurbita) Seed Protein; Organic Brown Rice Protein); Flaxseed Powder; Gum Blend (Cellulose; Xanthan); Salt; Amaranth Powder; Quinoa Powder; Organic Chia (Salvia Hispanica L.) Seed Powder; Coconut Powder; Organic Kale (Brassica Oleracea Acephala); Leaf Powder; Organic Broccoli (Brassica Oleracea Italica) Stem and Floret Powder; Organic Spinach (Spinacia Oleracea) Leaf Powder; Probiotic Blend (L. Acidophilus, Bifidobacterium Bifidum, Bifidobacterium Longum).", {
            title: "Ingredients",
            button: {
                text: "X",
                value: true,
                visible: true,
                className: "swal-button-cross",
                closeModal: true,
            },
        }
    );
};

const contentsAlert = () => {
    swal(
        "Plant Protein Blend (Pea Protein; Organic Pumpkin (Cucurbita) Seed Protein; Organic Brown Rice Protein); Flaxseed Powder; Gum Blend (Cellulose; Xanthan); Salt; Amaranth Powder; Quinoa Powder; Organic Chia (Salvia Hispanica L.) Seed Powder; Coconut Powder; Organic Kale (Brassica Oleracea Acephala); Leaf Powder; Organic Broccoli (Brassica Oleracea Italica) Stem and Floret Powder; Organic Spinach (Spinacia Oleracea) Leaf Powder; Probiotic Blend (L. Acidophilus, Bifidobacterium Bifidum, Bifidobacterium Longum).", {
            button: {
                text: "X",
                value: true,
                visible: true,
                className: "swal-button-cross",
                closeModal: true,
            },
        }
    );
};