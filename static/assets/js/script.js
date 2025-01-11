'use strict';

let tg = null;
let telegramId = null;

document.addEventListener('DOMContentLoaded', () => {
    // التحقق من توفر Telegram WebApp
    if (typeof Telegram === 'undefined' || typeof Telegram.WebApp === 'undefined') {
        console.error("Telegram WebApp غير متوفر. يرجى فتح التطبيق من داخل Telegram.");
        alert("يرجى فتح التطبيق من داخل Telegram.");
        return;
    }

    // تهيئة Telegram WebApp
    tg = Telegram.WebApp;

    tg.ready(() => {
        console.log("Telegram WebApp جاهز.");

        try {
            const initData = tg.initDataUnsafe;
            console.log("Init Data Unsafe:", initData);

            if (initData?.user?.id) {
                telegramId = initData.user.id;
                const username = initData.user.username || "Unknown User";
                const fullName = `${initData.user.first_name || ''} ${initData.user.last_name || ''}`.trim();

                console.log("Telegram ID:", telegramId);
                console.log("Username:", username);
                console.log("Full Name:", fullName);

                // تحديث واجهة المستخدم
                updateUserUI(fullName, username);

                // إرسال Telegram ID إلى الخادم
                sendTelegramIDToServer(telegramId, username);
            } else {
                console.error("بيانات المستخدم غير متوفرة.");
                alert("يرجى تشغيل التطبيق من داخل Telegram.");
            }
        } catch (error) {
            console.error("حدث خطأ أثناء الوصول إلى بيانات Telegram:", error);
            alert("حدث خطأ أثناء تهيئة التطبيق. يرجى المحاولة لاحقاً.");
        }
    });

    // إضافة الأحداث لأزرار الاشتراك والتجديد
    bindSubscriptionButtons();
});

// تحديث واجهة المستخدم
function updateUserUI(fullName, username) {
    const userNameElement = document.getElementById("user-name");
    const userUsernameElement = document.getElementById("user-username");

    if (userNameElement) userNameElement.textContent = fullName;
    if (userUsernameElement) userUsernameElement.textContent = username;
}

// إرسال Telegram ID إلى الخادم
function sendTelegramIDToServer(telegramId, username) {
    console.log("إرسال Telegram ID إلى الخادم...");
    sendApiRequest("verify", "POST", { telegramId, username })
        .then(response => console.log("تم التحقق من Telegram ID:", response))
        .catch(error => console.error("حدث خطأ أثناء التحقق من Telegram ID:", error));
}

// دالة عامة لإرسال الطلبات إلى API
function sendApiRequest(endpoint, method, data) {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: `https://exaado-mini-app-c04ea61e41f4.herokuapp.com/api/${endpoint}`,
            type: method,
            contentType: "application/json",
            data: JSON.stringify(data),
            beforeSend: showLoading,
            complete: hideLoading,
            success: function (response) {
                resolve(response);
            },
            error: function (error) {
                console.error(`Error during API call to ${endpoint}:`, error);
                reject(new Error(error.responseJSON?.error || "Unknown Error"));
            }
        });
    });
}

// إضافة الأحداث لأزرار الاشتراك والتجديد
function bindSubscriptionButtons() {
    document.querySelectorAll('.subscribe-btn, .renew-btn').forEach(button => {
        button.addEventListener('click', function () {
            const subscriptionType = this.getAttribute('data-subscription');
            const isRenew = this.classList.contains('renew-btn');
            if (isRenew) {
                renewSubscription(subscriptionType);
            } else {
                subscribe(subscriptionType);
            }
        });
    });
}

// دالة الاشتراك
function subscribe(subscriptionType) {
    if (!telegramId) {
        alert("Telegram ID غير متوفر.");
        return;
    }
    sendApiRequest("subscribe", "POST", { telegram_id: telegramId, subscription_type: subscriptionType })
        .then(response => alert(`🎉 ${response.message}`))
        .catch(error => alert(`خطأ أثناء الاشتراك: ${error.message}`));
}

// دالة التجديد
function renewSubscription(subscriptionType) {
    if (!telegramId) {
        alert("Telegram ID غير متوفر.");
        return;
    }
    sendApiRequest("renew", "POST", { telegram_id: telegramId, subscription_type: subscriptionType })
        .then(response => alert(`🎉 ${response.message}`))
        .catch(error => alert(`خطأ أثناء التجديد: ${error.message}`));
}

// دالة التحقق من الاشتراك
function checkSubscription(telegramId) {
    if (!telegramId) {
        alert("لا يمكن تنفيذ العملية: Telegram ID غير متوفر.");
        return;
    }

    sendApiRequest(`check_subscription?telegram_id=${telegramId}`, "GET")
        .then(response => console.log("User subscriptions:", response.subscriptions))
        .catch(error => alert("حدث خطأ أثناء التحقق من الاشتراك: " + error.message));
}

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
