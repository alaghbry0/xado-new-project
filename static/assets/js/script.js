'use strict';

let tg = null; // تعريف المتغير tg كمتحول عام
let telegramId = null; // تعريف telegramId كمتحول عام

function initializeTelegramWebApp() {
    try {
        tg = window.Telegram?.WebApp;

        if (!tg) {
            console.error("Telegram WebApp API not available.");
            alert("يرجى تشغيل التطبيق من داخل Telegram.");
            return;
        }

        tg.ready();
        tg.expand();
        console.log("Telegram WebApp initialized successfully!");
        console.log("Telegram WebApp initialized:", tg);
        console.log("Init Data:", tg.initData);
        console.log("Init Data Unsafe:", tg.initDataUnsafe);

        // استخراج بيانات المستخدم
        const userData = tg.initDataUnsafe?.user;
        if (userData && userData.id) {
            telegramId = userData.id;
            const username = userData.username || "Unknown User";
            const fullName = `${userData.first_name || ''} ${userData.last_name || ''}`.trim();

            console.log("Telegram ID:", telegramId);
            console.log("Username:", username);
            console.log("Full Name:", fullName);

            // عرض بيانات المستخدم على الصفحة
            const userNameElement = document.getElementById("user-name");
            const userUsernameElement = document.getElementById("user-username");

            if (userNameElement) userNameElement.textContent = fullName;
            if (userUsernameElement) userUsernameElement.textContent = username;
        } else {
            console.warn("User data not available.");
            alert("يرجى فتح التطبيق من داخل Telegram.");
        }
    } catch (error) {
        console.error("Error initializing Telegram WebApp:", error);
        alert("حدث خطأ أثناء تهيئة التطبيق. يرجى المحاولة لاحقاً.");
    }
}

// إضافة مهلة قصيرة للتأكد من تحميل tg بشكل كامل
window.onload = function () {
    setTimeout(() => {
        initializeTelegramWebApp();
    }, 200); // انتظار 200 ميلي ثانية قبل التهيئة
};



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
window.subscribe = function (subscriptionType) {
    if (!tg) {
        console.error("Telegram WebApp API not initialized.");
        alert("يرجى تشغيل التطبيق من داخل Telegram.");
        return;
    }

    if (!telegramId) {
        console.error("Telegram ID not available.");
        alert("لا يمكن الاشتراك: Telegram ID غير متوفر.");
        return;
    }

    const subscriptionData = {
        telegram_id: telegramId,
        subscription_type: subscriptionType
    };

    console.log("Data being sent for subscription:", subscriptionData);

    // إرسال البيانات إلى API
    subscribeToApi(subscriptionData)
        .then((response) => {
            console.log("Subscription response:", response);
            alert(`🎉 ${response.message}`);
        })
        .catch((error) => {
            console.error("Error during subscription:", error);
            alert("حدث خطأ أثناء الاشتراك: " + (error.message || "Unknown Error"));
        });
};

// دالة إرسال البيانات إلى API
function subscribeToApi(data) {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: "https://exaado-mini-app-c04ea61e41f4.herokuapp.com/api/subscribe",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(data),
            success: function (response) {
                resolve(response);
            },
            error: function (error) {
                console.error("AJAX Error:", error);
                reject(new Error(error.responseJSON?.error || "Unknown Error"));
            }
        });
    });
}

// إضافة الأحداث لأزرار الاشتراك
document.querySelectorAll('.subscribe-btn').forEach(button => {
    button.addEventListener('click', function () {
        const subscriptionType = this.getAttribute('data-subscription');
        subscribe(subscriptionType);
    });
});

// دالة التحقق من الاشتراك
function checkSubscription(telegramId) {
    if (!telegramId) {
        alert("لا يمكن تنفيذ العملية: Telegram ID غير متوفر.");
        return;
    }

    $.ajax({
        url: `/api/check_subscription?telegram_id=${telegramId}`,
        type: "GET",
        success: function (response) {
            console.log("User subscriptions:", response.subscriptions); // عرض بيانات الاشتراك
        },
        error: function (error) {
            console.error("Error checking subscription:", error);
            alert("حدث خطأ: " + (error.responseJSON?.error || "Unknown Error"));
        }
    });
}

// دالة التجديد
window.renewSubscription = function (subscriptionType) {
    if (!tg) {
        alert("يرجى تشغيل التطبيق من داخل Telegram.");
        return;
    }

    if (!telegramId) {
        alert("لا يمكن تنفيذ العملية: Telegram ID غير متوفر.");
        return;
    }

    const renewalData = {
        telegram_id: telegramId,
        subscription_type: subscriptionType
    };

    console.log("Data sent to server for renewal:", renewalData);

    showLoading();

    $.ajax({
        url: "/api/renew",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify(renewalData),
        success: function (response) {
            alert(response.message);
            console.log("Renewal successful:", response);
        },
        error: function (error) {
            console.error("Error during renewal:", error);
            alert("حدث خطأ أثناء التجديد: " + (error.responseJSON?.error || "Unknown Error"));
        },
        complete: function () {
            hideLoading();
        }
    });
};

// إضافة الأحداث لأزرار التجديد
document.querySelectorAll('.renew-btn').forEach(button => {
    button.addEventListener('click', function () {
        const subscriptionType = this.getAttribute('data-subscription');
        renewSubscription(subscriptionType);
    });
});

// التعامل مع الأحداث عند تحميل الصفحة
document.addEventListener("DOMContentLoaded", function () {
    // ربط الأحداث لأزرار الاشتراك
    document.querySelectorAll('.subscribe-btn').forEach(button => {
        button.addEventListener('click', function () {
            const subscriptionType = this.getAttribute('data-subscription');
            subscribe(subscriptionType);
        });
    });

    // ربط الأحداث لأزرار التجديد
    document.querySelectorAll('.renew-btn').forEach(button => {
        button.addEventListener('click', function () {
            const subscriptionType = this.getAttribute('data-subscription');
            renewSubscription(subscriptionType);
        });
    });
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
