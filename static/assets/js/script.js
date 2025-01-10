'use strict';

const tg = window.Telegram?.WebApp;

if (!tg) {
    console.error("Telegram WebApp API not available.");
    alert("يرجى تشغيل التطبيق من داخل Telegram.");
} else {
    tg.ready();
    tg.expand();
    console.log("Telegram WebApp initialized successfully!");
}


// Telegram WebApp Initialization
let telegramId = null; // تعريف telegramId كمتحول عام

window.onload = function () {
    if (!tg) {
        console.warn("Telegram WebApp API not available.");
        alert("يرجى تشغيل التطبيق من داخل Telegram.");
        return;
    }

    try {
        const userData = tg.initDataUnsafe?.user;
        if (userData && userData.id) {
            telegramId = userData.id;
            const username = userData.username || "Unknown User";
            const fullName = `${userData.first_name || ''} ${userData.last_name || ''}`.trim();

            console.log("Telegram ID:", telegramId);
            console.log("Username:", username);
            console.log("Full Name:", fullName);

            console.log("Global Telegram ID:", telegramId); // متاح الآن

            // عرض بيانات المستخدم
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
    }
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
        alert("يرجى تشغيل التطبيق من داخل Telegram.");
        return;
    }

    const telegramId = tg.initDataUnsafe?.user?.id;
    if (!telegramId) {
        alert("لا يمكن الاشتراك: Telegram ID غير متوفر.");
        return;
    }

    const base = {
        telegram_id: telegramId,
        subscription_type: subscriptionType
    };

    console.log("Data being sent for subscription:", base);

    // إنشاء العملية
    const result = subscribeToApi(base);

    if (result instanceof Promise) {
        result
            .then((response) => {
                console.log("Subscription response:", response);
                alert(`🎉 ${response.message}`);
            })
            .catch((error) => {
                console.error("Error during subscription:", error);
                alert("حدث خطأ أثناء الاشتراك: " + (error.message || "Unknown Error"));
            });
    } else {
        console.warn("Subscription did not return a Promise.");
    }
};



//داله subscribeToApi
function subscribeToApi(base) {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: "https://exaado-mini-app-c04ea61e41f4.herokuapp.com/api/subscribe",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(base),
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
            console.log(response.subscriptions); // عرض بيانات الاشتراك
        },
        error: function (error) {
            console.error("Error details:", error);
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

    const telegramId = tg.initDataUnsafe?.user?.id;
    if (!telegramId) {
        alert("لا يمكن تنفيذ العملية: Telegram ID غير متوفر.");
        return;
    }

    console.log("Data sent to server for renewal:", {
        telegram_id: telegramId,
        subscription_type: subscriptionType
    });

    showLoading();

    $.ajax({
        url: "/api/renew",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            telegram_id: telegramId,
            subscription_type: subscriptionType
        }),
        success: function (response) {
            alert(response.message);
            console.log("Renewal successful:", response);
        },
        error: function (error) {
            console.error("Error details:", error);
            const errorMessage = error.responseJSON?.error || "Unknown Error";
            alert("حدث خطأ أثناء التجديد: " + errorMessage);
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

// التعامل مع النقرات للأزرار
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

//ظهور شريط التحميل عند الاشتراك والتجديد
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


const tg = window.Telegram.WebApp;
console.log("Init Data:", tg.initData);
console.log(typeof subscribe); // يجب أن يظهر "function"
if (telegramId) {
    console.log("Telegram ID is:", telegramId);
} else {
    console.error("Telegram ID is not defined.");
}


if (!tg.initData) {
    alert("يرجى فتح التطبيق من داخل Telegram.");
}
