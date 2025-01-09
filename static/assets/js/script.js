'use strict'
// التحقق من أن Telegram WebApp متوفر
let telegramId = null;
let username = null;
let fullName = null;

try {
    if (window.Telegram && window.Telegram.WebApp) {
    const telegram = window.Telegram.WebApp;

    // التحقق من بيانات المستخدم
    if (telegram.initDataUnsafe && telegram.initDataUnsafe.user) {
        const telegramId = telegram.initDataUnsafe.user.id || null;
        const username = telegram.initDataUnsafe.user.username || "Unknown User";
        const fullName = `${telegram.initDataUnsafe.user.first_name || ''} ${telegram.initDataUnsafe.user.last_name || ''}`;

        console.log("Telegram ID:", telegramId);
        console.log("Username:", username);
        console.log("Full Name:", fullName);
    } else {
        alert("يرجى فتح التطبيق من داخل Telegram.");
    }
} else {
    alert("يرجى التأكد من تشغيل التطبيق داخل Telegram WebApp.");
}

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
if (telegramId) {
    const userNameElement = document.getElementById("user-name");
    const userUsernameElement = document.getElementById("user-username");
    const avatarElement = document.querySelector(".avatar img");

    if (userNameElement) {
        userNameElement.textContent = telegram.initDataUnsafe?.user?.first_name || "Unknown";
    }
    if (userUsernameElement) {
        userUsernameElement.textContent = telegram.initDataUnsafe?.user?.username || "Unknown User";
    }
    if (avatarElement) {
        avatarElement.src = "assets/img/default-profile.jpg"; // صورة افتراضية
    }
}

 else {
    alert("يرجى فتح التطبيق من داخل Telegram.");
}


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



// دالة الاشتراك
function subscribe(subscriptionType) {
    if (!telegramId) {
        alert("لا يمكن الاشتراك: Telegram ID غير متوفر.");
        return;
    }

    console.log("Subscription Type:", subscriptionType);

    $.ajax({
        url: "/api/subscribe",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            telegram_id: telegramId,
            subscription_type: subscriptionType
        }),
        success: function (response) {
            alert(`🎉 ${response.message}`);
        },
        error: function (error) {
            console.error("Error details:", error);
            alert("حدث خطأ أثناء الاشتراك: " + (error.responseJSON?.error || "Unknown Error"));
        }
    });
}

// دالة التحقق من الاشتراك
function checkSubscription(telegramId) {
    if (!telegramId) {
    alert("لا يمكن تنفيذ العملية: Telegram ID غير متوفر.");
    return;
}

    $.ajax({
        url: `/api/check_subscription?telegram_id=${telegramId}`,
        type: "GET",
        success: function(response) {
            console.log(response.subscriptions); // عرض بيانات الاشتراك في الكونسول
        },
        error: function(error) {
    console.error("Error details:", error);
    alert("حدث خطأ: " + (error.responseJSON?.error || "Unknown Error"));
}

    });
}

function renewSubscription(subscriptionType) {
    if (!telegramId) {
        alert("لا يمكن تنفيذ العملية: Telegram ID غير متوفر.");
        return;
    }

    showLoading(); // إظهار شريط التحميل

    $.ajax({
        url: "/api/renew",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            telegram_id: telegramId,
            subscription_type: subscriptionType
        }),
        success: function (response) {
            alert(response.message); // عرض رسالة النجاح
            // تحديث واجهة المستخدم إذا لزم الأمر
        },
        error: function (error) {
            console.error("Error details:", error);
            alert("حدث خطأ أثناء التجديد: " + (error.responseJSON?.error || "Unknown Error"));
        },
        complete: function () {
            hideLoading(); // إخفاء شريط التحميل
        }
    });
}

//ظهور شريط التحميل عند الاشتراك والتجديد

const tg = window.Telegram.WebApp;
console.log("Init Data:", tg.initData);

if (!tg.initData) {
    alert("يرجى فتح التطبيق من داخل Telegram.");
}




