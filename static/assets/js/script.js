'use strict';

// تعريف المتغيرات العامة
window.tg = null;
window.telegramId = null;

// دالة عامة لتنفيذ طلبات AJAX
window.performAjaxRequest = function ({ url, method = "GET", data = null, onSuccess, onError }) {
    $.ajax({
        url,
        type: method,
        contentType: "application/json",
        data: data ? JSON.stringify(data) : null,
        success: onSuccess,
        error: onError,
    });
};

// التهيئة الأساسية لتطبيق Telegram WebApp
window.initializeTelegramWebApp = function () {
    try {
        // تأكد من عدم إعادة تعريف tg
        if (window.tg) {
            console.log("Telegram WebApp API تم تهيئته مسبقًا.");
            return;
        }

        window.tg = window.Telegram?.WebApp;

        if (!window.tg) {
            window.handleError("Telegram WebApp API غير متوفر. يرجى فتح التطبيق من داخل Telegram.");
            return;
        }

        // تأكيد التهيئة
        window.tg.ready(() => {
            console.log("Telegram WebApp جاهز.");
            const userData = window.tg.initDataUnsafe?.user;

            if (userData?.id) {
                window.telegramId = userData.id;
                const username = userData.username || "Unknown User";
                const fullName = `${userData.first_name || ''} ${userData.last_name || ''}`.trim();

                console.log("Telegram ID:", window.telegramId);
                console.log("Username:", username);
                console.log("Full Name:", fullName);

                window.updateUserUI(fullName, username);
                window.sendTelegramIDToServer(window.telegramId, username);
            } else {
                window.handleError("بيانات المستخدم غير متوفرة بعد التهيئة.");
            }
        });
    } catch (error) {
        window.handleError("حدث خطأ أثناء تهيئة التطبيق: " + error.message);
    }
};

// تحديث واجهة المستخدم
window.updateUserUI = function (fullName, username) {
    const userNameElement = document.getElementById("user-name");
    const userUsernameElement = document.getElementById("user-username");

    if (userNameElement) userNameElement.textContent = fullName;
    if (userUsernameElement) userUsernameElement.textContent = username;
};

// إرسال Telegram ID إلى الخادم
window.sendTelegramIDToServer = function (telegramId, username) {
    window.performAjaxRequest({
        url: "/api/verify",
        method: "POST",
        data: { telegram_id: telegramId, username },
        onSuccess: (response) => console.log("تم التحقق من Telegram ID:", response),
        onError: (error) => console.error("حدث خطأ أثناء التحقق من Telegram ID:", error),
    });
};

// التعامل مع الأخطاء
window.handleError = function (message) {
    console.error(message);
    alert(message);
};

// التحقق من بيئة Telegram
window.checkTelegramEnvironment = function () {
    console.log("التحقق من بيئة Telegram WebApp...");
    console.log("window.Telegram:", window.Telegram);
    console.log("window.Telegram.WebApp:", window.Telegram?.WebApp);

    if (!window.Telegram || !window.Telegram.WebApp) {
        window.handleError("Telegram WebApp غير متوفر. يرجى فتح التطبيق من داخل Telegram.");
        return false;
    }

    console.log("Telegram.WebApp متوفر. التطبيق يعمل داخل Telegram WebApp.");
    return true;
};

// بدء التهيئة عند تحميل الصفحة
document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded and parsed.");

    // التحقق من Telegram WebApp
    if (window.checkTelegramEnvironment()) {
        window.initializeTelegramWebApp();
    } else {
        console.warn("Application running outside Telegram WebApp.");
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

// تحديث بيانات المستخدم وعرضها في واجهة المستخدم
window.updateUserUI = function () {
    if (!window.telegramId) {
        console.error("Telegram ID is not defined. Make sure the WebApp is initialized properly.");
        alert("يرجى فتح التطبيق من داخل Telegram.");
        return;
    }

    const userData = window.tg?.initDataUnsafe?.user;

    if (!userData) {
        console.error("User data is missing in Telegram WebApp.");
        return;
    }

    console.log("Telegram ID is valid. Proceeding to display user data...");

    const userNameElement = document.getElementById("user-name");
    const userUsernameElement = document.getElementById("user-username");
    const avatarElement = document.querySelector(".avatar img");

    if (userNameElement) {
        userNameElement.textContent = userData.first_name || "Unknown";
    }
    if (userUsernameElement) {
        userUsernameElement.textContent = userData.username || "Unknown User";
    }
    if (avatarElement) {
        avatarElement.src = userData.photo_url || "assets/img/default-profile.jpg"; // صورة افتراضية
    }
};




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

//داله الاشتراك
window.subscribe = function (subscriptionType) {
    console.log("بدء عملية الاشتراك...");

    if (!tg) {
        console.error("Telegram WebApp API غير مهيأ.");
        alert("يرجى تشغيل التطبيق من داخل Telegram.");
        return;
    }

    if (!telegramId) {
        console.error("Telegram ID غير متوفر.");
        alert("لا يمكن الاشتراك: Telegram ID غير متوفر.");
        return;
    }

    const subscriptionData = {
        telegram_id: telegramId,
        subscription_type: subscriptionType,
    };

    console.log("البيانات المرسلة للاشتراك:", subscriptionData);

    // إرسال البيانات إلى API
    window.performAjaxRequest({
        url: "https://exaado-mini-app-c04ea61e41f4.herokuapp.com/api/subscribe",
        method: "POST",
        data: subscriptionData,
        onSuccess: (response) => {
            console.log("تم الاشتراك بنجاح:", response);
            alert(`🎉 ${response.message}`);
        },
        onError: (error) => {
            console.error("خطأ أثناء عملية الاشتراك:", error);
            alert("حدث خطأ أثناء الاشتراك. يرجى المحاولة لاحقًا.");
        },
    });
};


// دالة التحقق من الاشتراك
window.checkSubscription = function (telegramId) {
    if (!telegramId) {
        console.error("Telegram ID غير متوفر. لا يمكن التحقق من الاشتراك.");
        alert("Telegram ID غير متوفر. لا يمكن التحقق من الاشتراك.");
        return;
    }

    window.performAjaxRequest({
        url: `/api/check_subscription?telegram_id=${telegramId}`,
        method: "GET",
        onSuccess: (response) => {
            console.log("تفاصيل الاشتراك:", response.subscriptions);
        },
        onError: (error) => {
            console.error("خطأ أثناء التحقق من الاشتراك:", error);
            alert("حدث خطأ أثناء التحقق من الاشتراك. يرجى المحاولة لاحقًا.");
        },
    });
};

//داله التجديد
window.renewSubscription = function (subscriptionType) {
    console.log("بدء عملية التجديد...");

    if (!tg) {
        console.error("Telegram WebApp API غير مهيأ.");
        alert("يرجى تشغيل التطبيق من داخل Telegram.");
        return;
    }

    if (!telegramId) {
        console.error("Telegram ID غير متوفر.");
        alert("لا يمكن تنفيذ العملية: Telegram ID غير متوفر.");
        return;
    }

    const renewalData = {
        telegram_id: telegramId,
        subscription_type: subscriptionType,
    };

    console.log("البيانات المرسلة للتجديد:", renewalData);

    // إرسال بيانات التجديد إلى API
    window.performAjaxRequest({
        url: "https://exaado-mini-app-c04ea61e41f4.herokuapp.com/api/renew",
        method: "POST",
        data: renewalData,
        onSuccess: (response) => {
            console.log("تم التجديد بنجاح:", response);
            alert(`🎉 ${response.message}`);
        },
        onError: (error) => {
            console.error("خطأ أثناء عملية التجديد:", error);
            alert("حدث خطأ أثناء التجديد. يرجى المحاولة لاحقًا.");
        },
    });
};

// ربط الأحداث لأزرار
window.bindButtonEvents = function () {
    document.querySelectorAll(".subscribe-btn").forEach((button) => {
        button.addEventListener("click", function () {
            const subscriptionType = this.getAttribute("data-subscription");
            if (!subscriptionType) {
                console.error("نوع الاشتراك غير محدد.");
                return;
            }
            window.subscribe(subscriptionType);
        });
    });

    document.querySelectorAll(".renew-btn").forEach((button) => {
        button.addEventListener("click", function () {
            const subscriptionType = this.getAttribute("data-subscription");
            if (!subscriptionType) {
                console.error("نوع التجديد غير محدد.");
                return;
            }
            window.renewSubscription(subscriptionType);
        });
    });
};


// التعامل مع الأحداث عند تحميل الصفحة
document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded and parsed.");

    // ربط الأحداث
    window.bindButtonEvents();

    // التحقق من Telegram WebApp
    if (checkTelegramEnvironment()) {
        initializeTelegramWebApp();
    } else {
        console.warn("Application running outside Telegram WebApp.");
    }
});


// دوال التحكم بشريط التحميل
function showLoading() {
    const loader = document.getElementById("loader");
    if (loader) {
        loader.style.display = "block";
    }
}

function hideLoading() {
    const loader = document.getElementById("loader");
    if (loader) {
        loader.style.display = "none";
    }
}
