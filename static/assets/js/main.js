// الحصول على بيانات المستخدم من Telegram Web App
const telegram = window.Telegram.WebApp;
const telegramId = telegram.initDataUnsafe.user.id; // Telegram ID
const username = telegram.initDataUnsafe.user.username; // اسم المستخدم
const fullName = telegram.initDataUnsafe.user.first_name + " " + telegram.initDataUnsafe.user.last_name; // الاسم الكامل

console.log("Telegram ID:", telegramId);
console.log("Username:", username);
console.log("Full Name:", fullName);

'use strict'
$(document).ready(function () {

    var body = $('body');
    var bodyParent = $('html');

    /* page load as iframe */
    if (self !== top) {
        body.addClass('iframe');
    } else {
        body.removeClass('iframe');
    }

    /* menu open close */
    $('.menu-btn').on('click', function () {
        if (body.hasClass('menu-open') === true) {
            body.removeClass('menu-open');
            bodyParent.removeClass('menu-open');
        } else {
            body.addClass('menu-open');
            bodyParent.addClass('menu-open');
        }

        return false;
    });

    body.on("click", function (e) {
        if (!$('.sidebar').is(e.target) && $('.sidebar').has(e.target).length === 0) {
            body.removeClass('menu-open');
            bodyParent.removeClass('menu-open');
        }

        return true;
    });



    /* menu style switch */
    $('#menu-pushcontent').on('change', function () {
        if ($(this).is(':checked') === true) {
            body.addClass('menu-push-content');
            body.removeClass('menu-overlay');
        }

        return false;
    });

    $('#menu-overlay').on('change', function () {
        if ($(this).is(':checked') === true) {
            body.removeClass('menu-push-content');
            body.addClass('menu-overlay');
        }

        return false;
    });

    // بيانات المستخدم (أمثلة)
const userData = {
    name: "محمد أحمد",
    username: "@mohamedahmed",
    profileImage: "assets/img/user1.jpg" // رابط صورة الملف الشخصي
};

// تحديث بيانات المستخدم في القائمة
document.getElementById("user-name").textContent = userData.name;
document.getElementById("user-username").textContent = userData.username;
document.querySelector(".avatar img").src = userData.profileImage;



    /* back page navigation */
    $('.back-btn').on('click', function () {
        window.history.back();

        return false;
    });

    /* Filter button */
    $('.filter-btn').on('click', function () {
        if (body.hasClass('filter-open') === true) {
            body.removeClass('filter-open');
        } else {
            body.addClass('filter-open');
        }

        return false;
    });
    $('.filter-close').on('click', function () {
        if (body.hasClass('filter-open') === true) {
            body.removeClass('filter-open');
        }
    });

    /* scroll y limited container height on page  */
    var scrollyheight = Number($(window).height() - $('.header').outerHeight() - $('.footer-info').outerHeight()) - 40;
    $('.scroll-y').height(scrollyheight);

});


$(window).on('load', function () {
    setTimeout(function () {
        $('.loader-wrap').fadeOut('slow');
    }, 500);

    /* coverimg */
    $('.coverimg').each(function () {
        var imgpath = $(this).find('img');
        $(this).css('background-image', 'url(' + imgpath.attr('src') + ')');
        imgpath.hide();
    })

    /* main container minimum height set */
    if ($('.header').length > 0 && $('.footer-info').length > 0) {
        var heightheader = $('.header').outerHeight();
        var heightfooter = $('.footer-info').outerHeight();

        var containerheight = $(window).height() - heightheader - heightfooter - 2;
        $('.main-container ').css('min-height', containerheight);
    }


    /* url path on menu */
    var path = window.location.href; // because the 'href' property of the DOM element is the absolute path
    $(' .main-menu ul a').each(function () {
        if (this.href === path) {
            $(' .main-menu ul a').removeClass('active');
            $(this).addClass('active');
        }
    });

});

$(window).on('scroll', function () {


    /* scroll from top and add class */
    if ($(document).scrollTop() > '10') {
        $('.header').addClass('active');
    } else {
        $('.header').removeClass('active');
    }
});


$(window).on('resize', function () {
    /* main container minimum height set */
    if ($('.header').length > 0 && $('.footer-info').length > 0) {
        var heightheader = $('.header').outerHeight();
        var heightfooter = $('.footer-info').outerHeight();

        var containerheight = $(window).height() - heightheader - heightfooter;
        $('.main-container ').css('min-height', containerheight);
    }
});


function subscribe(subscriptionType) {
    $.ajax({
        url: "/api/subscribe",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            telegram_id: telegramId, // استخدم Telegram ID الديناميكي
            subscription_type: subscriptionType
        }),
        success: function(response) {
            alert(response.message); // عرض رسالة النجاح
        },
        error: function(error) {
            alert("حدث خطأ: " + error.responseJSON.error);
        }
    });
}


function subscribe(subscriptionType) {
    if (typeof telegramId === 'undefined') {
        alert("لا يمكن الاشتراك: Telegram ID غير متوفر.");
        return;
    }

    $.ajax({
        url: "/api/subscribe",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            telegram_id: telegramId, // Telegram ID الديناميكي
            subscription_type: subscriptionType
        }),
        success: function(response) {
            alert(`🎉 ${response.message}`); // عرض رسالة النجاح
        },
        error: function(error) {
            alert("حدث خطأ: " + error.responseJSON.error);
        }
    });
}



function checkSubscription(telegramId) {
    $.ajax({
        url: `/api/check_subscription?telegram_id=${telegramId}`,
        type: "GET",
        success: function(response) {
            console.log(response.subscriptions); // عرض بيانات الاشتراك في الكونسول
        },
        error: function(error) {
            alert("حدث خطأ: " + error.responseJSON.message);
        }
    });
}
console.log("Telegram ID:", telegramId);

// التحقق من أن Telegram WebApp متوفر
if (window.Telegram && window.Telegram.WebApp) {
    const telegram = window.Telegram.WebApp;
    const telegramId = telegram.initDataUnsafe?.user?.id; // Telegram ID
    const username = telegram.initDataUnsafe?.user?.username; // اسم المستخدم
    const fullName = `${telegram.initDataUnsafe?.user?.first_name || ''} ${telegram.initDataUnsafe?.user?.last_name || ''}`; // الاسم الكامل

    console.log("Telegram ID:", telegramId);
    console.log("Username:", username);
    console.log("Full Name:", fullName);
} else {
    console.error("Telegram WebApp is not available. Please ensure the app is opened within Telegram.");
    alert("يرجى فتح التطبيق من داخل Telegram.");
}


