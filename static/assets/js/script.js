'use strict';

// تعريف المتغيرات العامة
let tg = null;
let telegramId = null;

// دالة عامة لتنفيذ طلبات AJAX
function performAjaxRequest({ url, method = "GET", data = null, onSuccess, onError }) {
    $.ajax({
        url,
        type: method,
        contentType: "application/json",
        data: data ? JSON.stringify(data) : null,
        success: onSuccess,
        error: onError,
    });
}

// التهيئة الأساسية لتطبيق Telegram WebApp
function initializeTelegramWebApp() {
    try {
        tg = window.Telegram?.WebApp;

        if (!tg) {
            handleError("Telegram WebApp API غير متوفر. يرجى فتح التطبيق من داخل Telegram.");
            return;
        }

        // تأكيد التهيئة
        tg.ready(() => {
            console.log("Telegram WebApp جاهز.");
            const userData = tg.initDataUnsafe?.user;

            if (userData?.id) {
                telegramId = userData.id;
                const username = userData.username || "Unknown User";
                const fullName = `${userData.first_name || ''} ${userData.last_name || ''}`.trim();

                console.log("Telegram ID:", telegramId);
                console.log("Username:", username);
                console.log("Full Name:", fullName);

                updateUserUI(fullName, username);
                sendTelegramIDToServer(telegramId, username);
            } else {
                handleError("بيانات المستخدم غير متوفرة بعد التهيئة.");
            }
        });
    } catch (error) {
        handleError("حدث خطأ أثناء تهيئة التطبيق: " + error.message);
    }
}

// تحديث واجهة المستخدم
function updateUserUI(fullName, username) {
    const userNameElement = document.getElementById("user-name");
    const userUsernameElement = document.getElementById("user-username");

    if (userNameElement) userNameElement.textContent = fullName;
    if (userUsernameElement) userUsernameElement.textContent = username;
}

// إرسال Telegram ID إلى الخادم
function sendTelegramIDToServer(telegramId, username) {
    performAjaxRequest({
        url: "/api/verify",
        method: "POST",
        data: { telegram_id: telegramId, username },
        onSuccess: (response) => console.log("تم التحقق من Telegram ID:", response),
        onError: (error) => console.error("حدث خطأ أثناء التحقق من Telegram ID:", error),
    });
}

// التعامل مع الأخطاء
function handleError(message) {
    console.error(message);
    alert(message);
}

// التحقق من بيئة Telegram
function checkTelegramEnvironment() {
    console.log("التحقق من بيئة Telegram WebApp...");
    if (!window.Telegram || !window.Telegram.WebApp) {
        handleError("Telegram WebApp غير متوفر. يرجى فتح التطبيق من داخل Telegram.");
        return false;
    }
    console.log("Telegram.WebApp متوفر. التطبيق يعمل داخل Telegram WebApp.");
    return true;
}

// بدء التهيئة عند تحميل الصفحة
document.addEventListener("DOMContentLoaded", function () {
    if (checkTelegramEnvironment()) {
        initializeTelegramWebApp();
    }
});

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

    console.log("Telegram ID is valid. Proceeding to display user data...");

    if (userNameElement) {
        userNameElement.textContent = tg.initDataUnsafe?.user?.first_name || "Unknown";
    }
    if (userUsernameElement) {
        userUsernameElement.textContent = tg.initDataUnsafe?.user?.username || "Unknown User";
    }
    if (avatarElement) {
        avatarElement.src = tg.initDataUnsafe?.user?.photo_url || "assets/img/default-profile.jpg"; // صورة افتراضية
    }
} else {
    console.error("Telegram ID is not defined. Make sure the WebApp is initialized properly.");
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
    console.log("بدء عملية الاشتراك...");

    if (!tg) {
        handleError("Telegram WebApp API غير مهيأ. يرجى فتح التطبيق من داخل Telegram.");
        return;
    }

    if (!telegramId) {
        handleError("Telegram ID غير متوفر.");
        return;
    }

    const subscriptionData = {
        telegram_id: telegramId,
        subscription_type: subscriptionType,
    };

    console.log("البيانات المرسلة للاشتراك:", subscriptionData);

    // إرسال البيانات إلى API
    performAjaxRequest({
        url: "https://exaado-mini-app-c04ea61e41f4.herokuapp.com/api/subscribe",
        method: "POST",
        data: subscriptionData,
        onSuccess: (response) => {
            console.log("تم الاشتراك بنجاح:", response);
            alert(`🎉 ${response.message}`);
        },
        onError: (error) => {
            console.error("خطأ أثناء عملية الاشتراك:", error);
            handleError("حدث خطأ أثناء الاشتراك. يرجى المحاولة لاحقًا.");
        },
    });
}

// دالة التجديد
function renewSubscription(subscriptionType) {
    console.log("بدء عملية التجديد...");

    if (!tg) {
        handleError("Telegram WebApp API غير مهيأ. يرجى فتح التطبيق من داخل Telegram.");
        return;
    }

    if (!telegramId) {
        handleError("Telegram ID غير متوفر.");
        return;
    }

    const renewalData = {
        telegram_id: telegramId,
        subscription_type: subscriptionType,
    };

    console.log("البيانات المرسلة للتجديد:", renewalData);

    // إرسال بيانات التجديد إلى API
    performAjaxRequest({
        url: "https://exaado-mini-app-c04ea61e41f4.herokuapp.com/api/renew",
        method: "POST",
        data: renewalData,
        onSuccess: (response) => {
            console.log("تم التجديد بنجاح:", response);
            alert(`🎉 ${response.message}`);
        },
        onError: (error) => {
            console.error("خطأ أثناء عملية التجديد:", error);
            handleError("حدث خطأ أثناء التجديد. يرجى المحاولة لاحقًا.");
        },
    });
}


// دالة التحقق من الاشتراك
function checkSubscription(telegramId) {
    if (!telegramId) {
        handleError("Telegram ID غير متوفر. لا يمكن التحقق من الاشتراك.");
        return;
    }

    performAjaxRequest({
        url: `/api/check_subscription?telegram_id=${telegramId}`,
        method: "GET",
        onSuccess: (response) => {
            console.log("تفاصيل الاشتراك:", response.subscriptions);
        },
        onError: (error) => {
            console.error("خطأ أثناء التحقق من الاشتراك:", error);
            handleError("حدث خطأ أثناء التحقق من الاشتراك. يرجى المحاولة لاحقًا.");
        },
    });
}

// توحيد ربط الأحداث لجميع الأزرار
function bindButtonEvents() {
    document.querySelectorAll(".subscribe-btn").forEach((button) => {
        button.addEventListener("click", function () {
            const subscriptionType = this.getAttribute("data-subscription");
            if (!subscriptionType) {
                handleError("نوع الاشتراك غير محدد.");
                return;
            }
            subscribe(subscriptionType);
        });
    });

    document.querySelectorAll(".renew-btn").forEach((button) => {
        button.addEventListener("click", function () {
            const subscriptionType = this.getAttribute("data-subscription");
            if (!subscriptionType) {
                handleError("نوع التجديد غير محدد.");
                return;
            }
            renewSubscription(subscriptionType);
        });
    });
}

// تهيئة الأحداث عند تحميل الصفحة
document.addEventListener("DOMContentLoaded", function () {
    bindButtonEvents();
});


// التعامل مع الأحداث عند تحميل الصفحة
ocument.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded and parsed.");

// تهيئة الأحداث للأزرار
    bindButtonEvents();

// التحقق من Telegram WebApp
    if (checkTelegramEnvironment()) {
        initializeTelegramWebApp();
    } else {
        console.warn("Application running outside Telegram WebApp.");
    }
});

// دوال التحكم بشريط التحميل
function toggleLoader(visible) {
    const loader = document.getElementById("loader");
    if (loader) {
        loader.style.display = visible ? "block" : "none";
    } else {
        console.warn("Loader element not found in the DOM.");
    }
}
