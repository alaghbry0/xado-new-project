'use strict';

// تعريف المتغيرات العامة
window.tg = null;
window.telegramId = null;

// دالة عامة لتنفيذ طلبات AJAX
window.performAjaxRequest = function ({ url, method = "GET", data = null, onSuccess, onError }) {
    try {
        $.ajax({
            url,
            type: method,
            contentType: "application/json",
            data: data ? JSON.stringify(data) : null,
            success: onSuccess,
            error: onError,
        });
    } catch (error) {
        console.error("Error in performAjaxRequest:", error);
    }
};

// دالة للحصول على Telegram ID بشكل غير متزامن
window.getTelegramId = function () {
    return new Promise((resolve, reject) => {
        try {
            const tg = window.Telegram?.WebApp;
            const userData = tg?.initDataUnsafe?.user;

            if (userData?.id) {
                resolve(userData.id);
            } else {
                reject("Telegram ID غير متوفر. تأكد من تشغيل التطبيق داخل Telegram.");
            }
        } catch (error) {
            reject("حدث خطأ أثناء الحصول على Telegram ID: " + error.message);
        }
    });
};

// التهيئة الأساسية لتطبيق Telegram WebApp
window.initializeTelegramWebApp = function () {
    try {
        // التحقق من التهيئة السابقة
        if (window.tg) {
            console.log("Telegram WebApp API تم تهيئته مسبقًا.");
            return;
        }

        // تهيئة Telegram WebApp API
        window.tg = window.Telegram?.WebApp;

        if (!window.tg) {
            window.handleError("Telegram WebApp API غير متوفر. يرجى فتح التطبيق من داخل Telegram.");
            return;
        }

        // تأكيد الجاهزية
        window.tg.ready(() => {
            console.log("Telegram WebApp جاهز.");

            // استخراج Telegram ID
            window.getTelegramId()
                .then((telegramId) => {
                    window.telegramId = telegramId; // تخزين Telegram ID
                    console.log("Telegram ID:", window.telegramId);

                    // تحديث واجهة المستخدم
                    const username = window.tg.initDataUnsafe?.user?.username || "Unknown User";
                    const fullName = `${window.tg.initDataUnsafe?.user?.first_name || ''} ${window.tg.initDataUnsafe?.user?.last_name || ''}`.trim();

                    console.log("Username:", username);
                    console.log("Full Name:", fullName);

                    window.updateUserUI(fullName, username);

                    // إرسال Telegram ID إلى الخادم
                    window.sendTelegramIDToServer(window.telegramId, username);
                })
                .catch((error) => {
                    console.error(error);
                    window.handleError(error);
                });
        });
    } catch (error) {
        window.handleError("حدث خطأ أثناء تهيئة التطبيق: " + error.message);
    }
};

// تحديث واجهة المستخدم
window.updateUserUI = function (fullName, username) {
    try {
        // تحديث العناصر في واجهة المستخدم
        const userNameElement = document.getElementById("user-name");
        const userUsernameElement = document.getElementById("user-username");

        if (userNameElement) userNameElement.textContent = fullName;
        if (userUsernameElement) userUsernameElement.textContent = username;

        console.log("تم تحديث واجهة المستخدم.");
    } catch (error) {
        console.error("Error in updateUserUI:", error);
    }
};

// إرسال Telegram ID إلى الخادم
window.sendTelegramIDToServer = function (telegramId, username) {
    console.log("إرسال Telegram ID إلى الخادم...");
    window.performAjaxRequest({
        url: "/api/verify", // رابط API للتحقق
        method: "POST",
        data: { telegram_id: telegramId, username },
        onSuccess: (response) => {
            console.log("تم التحقق من Telegram ID بنجاح:", response);
        },
        onError: (error) => {
            console.error("حدث خطأ أثناء التحقق من Telegram ID:", error);
        },
    });
};

// التعامل مع الأخطاء
window.handleError = function (message) {
    console.error("خطأ:", message);
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
        console.warn("التطبيق يعمل خارج بيئة Telegram WebApp.");
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

// دالة الاشتراك
window.subscribe = async function (subscriptionTypeId) {
    console.log("بدء عملية الاشتراك...");

    try {
        // التحقق من Telegram ID
        if (!window.telegramId) {
            console.warn("Telegram ID غير متوفر. محاولة الحصول عليه...");
            const telegramId = await window.getTelegramId(); // استدعاء الدالة للحصول على Telegram ID
            window.telegramId = telegramId; // تخزين Telegram ID في المتغير العام
            console.log("Telegram ID تم تعيينه أثناء الاشتراك:", telegramId);
        }

        // إعداد بيانات الاشتراك
        const subscriptionData = {
            telegram_id: window.telegramId, // استخدام Telegram ID المخزن عالميًا
            subscription_type_id: subscriptionTypeId, // استخدام id الخاص بـ subscription_types
        };

        console.log("البيانات المرسلة للاشتراك:", subscriptionData);

        // إرسال بيانات الاشتراك إلى API
        window.performAjaxRequest({
            url: "https://xado-new-project.onrender.com/api/subscribe", // رابط API
            method: "POST",
            data: subscriptionData,
            onSuccess: (response) => {
                console.log("تم الاشتراك بنجاح:", response);
                alert(`🎉 ${response.message}`); // عرض رسالة نجاح
            },
            onError: (error) => {
                console.error("خطأ أثناء عملية الاشتراك:", error);
                alert("❌ حدث خطأ أثناء الاشتراك. يرجى المحاولة لاحقًا.");
            },
        });
    } catch (error) {
        console.error("حدث خطأ أثناء الاشتراك:", error);
        alert("❌ حدث خطأ أثناء الاشتراك. يرجى التأكد من تشغيل التطبيق من داخل Telegram.");
    }
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

    if (!window.tg) {
        console.error("Telegram WebApp API غير مهيأ.");
        alert("يرجى تشغيل التطبيق من داخل Telegram.");
        return;
    }

    const userData = window.tg.initDataUnsafe?.user;
    if (!userData || !userData.id) {
        console.error("Telegram ID غير متوفر بعد التهيئة.");
        alert("لا يمكن تنفيذ العملية: Telegram ID غير متوفر.");
        return;
    }

    const telegramId = userData.id;

    const renewalData = {
        telegram_id: telegramId,
        subscription_type: subscriptionType,
    };

    console.log("البيانات المرسلة للتجديد:", renewalData);

    // إرسال بيانات التجديد إلى API
    window.performAjaxRequest({
        url: "https://xado-new-project.onrender.com/api/renew",
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


document.addEventListener('DOMContentLoaded', async function () {
    console.log("DOM fully loaded and parsed.");

    // التحقق من وجود العنصر قبل التهيئة
    const buttonElement = document.getElementById('ton-connect-button');
    if (!buttonElement) {
        console.error("❌ عنصر ton-connect-button غير موجود في المستند.");
        return;
    }

    // التحقق من تحميل مكتبة TonConnect UI
    if (typeof TON_CONNECT_UI === 'undefined') {
        console.error("TON Connect UI SDK غير متوفر.");
        alert("❌ TON Connect UI SDK غير متوفر.");
        return;
    }

    // التحقق من Telegram ID
    if (!window.telegramId) {
        try {
            const telegramId = await window.getTelegramId(); // استخدام الدالة المضافة في الكود الأساسي
            window.telegramId = telegramId;
            console.log("Telegram ID تم تعيينه:", telegramId);
        } catch (error) {
            console.error(error);
            alert("❌ حدث خطأ أثناء الحصول على Telegram ID: " + error.message);
            return;
        }
    } else {
        console.log("Telegram ID متوفر:", window.telegramId);
    }

    // تحميل manifest يدويًا باستخدام fetch
    let manifestData = null;
    try {
        const response = await fetch('https://xado-new-project.onrender.com/tonconnect-manifest.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        manifestData = await response.json();
        console.log('Manifest loaded successfully:', manifestData);
        alert("🎉 Manifest تم تحميله بنجاح!");
    } catch (error) {
        console.error('❌ Error loading manifest:', error);
        alert("❌ حدث خطأ أثناء تحميل Manifest. يرجى التحقق من الرابط أو إعدادات الخادم.");
        return; // إنهاء العملية إذا فشل تحميل manifest
    }

    // تهيئة TonConnectUI باستخدام manifest المحمل
    try {
        const tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
            manifest: manifestData, // تمرير البيانات المحملة يدويًا
            buttonRootId: 'ton-connect-button', // ID عنصر HTML لزر ربط المحفظة
            uiOptions: {
                twaReturnUrl: 'https://t.me/Te20s25tbot' // رابط العودة لتطبيق Telegram
            }
        });

        console.log("Ton Connect UI initialized successfully.");

        // التعامل مع استجابة ربط المحفظة
        tonConnectUI.onStatusChange((wallet) => {
            if (wallet) {
                console.log('Wallet connected:', wallet);
                console.log('Telegram ID:', window.telegramId); // عرض Telegram ID
                alert(`🎉 Wallet connected: ${wallet.account}`);
                // إرسال بيانات المحفظة إلى الخادم
                window.sendWalletInfoToServer(wallet.account, window.telegramId);
            } else {
                console.log('Wallet disconnected');
                alert("⚠️ Wallet disconnected.");
            }
        });
    } catch (error) {
        console.error("❌ حدث خطأ أثناء تهيئة TonConnect UI:", error);
        alert("❌ حدث خطأ أثناء تهيئة TonConnect UI.");
    }
});

window.sendWalletInfoToServer = function (walletAddress, telegramId) {
    // إذا كان walletAddress كائنًا، استخراج العنوان النصي فقط
    const formattedWalletAddress = typeof walletAddress === "object" && walletAddress.address
        ? walletAddress.address
        : walletAddress; // إذا كان نصًا، استخدمه كما هو

    console.log("إرسال بيانات المحفظة إلى الخادم...");
    console.log("Telegram ID:", telegramId);
    console.log("Wallet Address:", formattedWalletAddress);

    window.performAjaxRequest({
        url: "/api/link-wallet",
        method: "POST",
        data: {
            wallet_address: formattedWalletAddress, // إرسال العنوان النصي فقط
            telegram_id: telegramId,
        },
        onSuccess: (response) => {
            console.log("تم ربط المحفظة بنجاح:", response);
            alert("🎉 تم ربط المحفظة بنجاح!");
        },
        onError: (error) => {
            console.error("خطأ أثناء ربط المحفظة:", error);
            alert("❌ حدث خطأ أثناء ربط المحفظة. يرجى المحاولة لاحقًا.");
        },
    });
};
