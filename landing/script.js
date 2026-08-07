// ============================================================================
// SI Filings Pro — Cloudflare Pages Frontend Engine
// Communicates with Vercel Serverless Backend & Neon PostgreSQL Database
// ============================================================================

const CLOUD_API_URL = "https://sifilings.vercel.app"; // Live production Vercel domain

// Modal DOM References
const registerModal = document.getElementById("register-modal");
const rechargeModal = document.getElementById("recharge-modal");

// ============================================================================
// Modal & UI Controls
// ============================================================================

function openFreeRegistration() {
    document.getElementById("firm-reg-form").style.display = "block";
    document.getElementById("reg-result-box").style.display = "none";
    document.getElementById("reg-modal-title").innerText = "🎁 Activate Your Firm Account";
    document.getElementById("reg-modal-sub").style.display = "block";
    registerModal.style.display = "flex";
}

function closeRegisterModal() {
    registerModal.style.display = "none";
}

function openRechargeModal(packName, price) {
    document.getElementById("recharge-pack-display").innerText = `${packName} — ₹${price}`;
    document.getElementById("recharge-amount-val").value = price;
    document.getElementById("recharge-status").style.display = "none";
    rechargeModal.style.display = "flex";
}

function closeRechargeModal() {
    rechargeModal.style.display = "none";
}

// Close modals when clicking outside content area
window.onclick = function(event) {
    if (event.target === registerModal) closeRegisterModal();
    if (event.target === rechargeModal) closeRechargeModal();
};

// ============================================================================
// API Handlers: Firm Registration & Free Trial Activation
// ============================================================================

async function handleFirmRegistration(event) {
    event.preventDefault();

    const firmName = document.getElementById("reg-firm-name").value.trim();
    const email = document.getElementById("reg-email").value.trim().toLowerCase();
    const submitBtn = document.getElementById("reg-submit-btn");

    submitBtn.disabled = true;
    submitBtn.innerText = "⏳ Connecting to Neon DB & Issuing Key...";

    try {
        const resp = await fetch(`${CLOUD_API_URL}/api/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ firm_name: firmName, email: email })
        });

        const data = await resp.json();

        if (resp.ok) {
            const acc = data.account || {};
            const licenseKey = acc.license_key || "SFP-DEMO-TEST-KEY";
            
            // Show celebratory screen
            document.getElementById("firm-reg-form").style.display = "none";
            document.getElementById("reg-modal-title").innerText = "✨ License Activated!";
            document.getElementById("reg-modal-sub").style.display = "none";
            document.getElementById("display-license-key").innerText = licenseKey;
            document.getElementById("reg-result-box").style.display = "block";
        } else {
            alert(data.error || "Failed to register firm account. Please verify your email.");
        }
    } catch (err) {
        console.error("Registration failed:", err);
        alert("⚠️ Cloud backend communication timed out. Ensure https://sifilings.vercel.app is accessible.");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "⚡ Generate License Key & Deposit 100 Credits";
    }
}

// ============================================================================
// Live Credit Wallet Metering Test (Hero Widget)
// ============================================================================

async function checkLiveWallet() {
    const keyInput = document.getElementById("testLicenseKey");
    const feedback = document.getElementById("walletFeedback");
    const key = keyInput.value.trim().toUpperCase();

    if (!key) {
        alert("Please paste your SFP-XXXX-XXXX-XXXX license key first!");
        return;
    }

    feedback.style.display = "block";
    feedback.innerHTML = "⏳ Querying Vercel & Neon cloud tables...";
    feedback.style.background = "#0e1422";
    feedback.style.color = "#38bdf8";
    feedback.style.borderColor = "#242f4c";

    try {
        const resp = await fetch(`${CLOUD_API_URL}/api/license/validate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ license_key: key })
        });

        const data = await resp.json();

        if (resp.ok) {
            feedback.style.background = "rgba(16, 185, 129, 0.12)";
            feedback.style.borderColor = "#10b981";
            feedback.style.color = "#a7f3d0";
            feedback.innerHTML = `✅ <strong>Firm Found:</strong> ${data.firm_name} (${data.customer_email})<br>` +
                                 `💎 <strong>Wallet Balance:</strong> <span style="font-size: 16px; font-weight: bold; color: #10b981;">${data.credits_balance} SI Credits</span> available!`;
        } else {
            feedback.style.background = "rgba(239, 68, 68, 0.12)";
            feedback.style.borderColor = "#ef4444";
            feedback.style.color = "#fca5a5";
            feedback.innerHTML = `❌ <strong>License Invalid:</strong> ${data.error || "Key not found in database."}`;
        }
    } catch (err) {
        feedback.style.background = "rgba(245, 158, 11, 0.12)";
        feedback.style.borderColor = "#f59e0b";
        feedback.style.color = "#fde68a";
        feedback.innerHTML = `⚠️ Could not reach cloud server at ${CLOUD_API_URL}.`;
    }
}

// ============================================================================
// Payment & Recharge Handlers
// ============================================================================

async function handleRechargeSubmit(event) {
    event.preventDefault();

    const email = document.getElementById("recharge-email").value.trim().toLowerCase();
    const amount = parseInt(document.getElementById("recharge-amount-val").value || "5999");
    const submitBtn = document.getElementById("recharge-submit-btn");
    const statusBox = document.getElementById("recharge-status");

    const packageKey = amount === 14999 ? "enterprise" : "pro";
    const payMode = "RAZORPAY";

    submitBtn.disabled = true;
    submitBtn.innerText = "⏳ Initializing Secure Checkout...";
    statusBox.style.display = "block";
    statusBox.innerHTML = "Processing invoice request...";
    statusBox.style.background = "#0e1422";
    statusBox.style.color = "#38bdf8";

    try {
        const resp = await fetch(`${CLOUD_API_URL}/api/billing/recharge`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email, package: packageKey, mode: payMode })
        });

        const data = await resp.json();

        if (resp.ok) {
            if (data.payment_mode === "RAZORPAY" && data.razorpay_order_id) {
                statusBox.innerHTML = `⏳ Opening Razorpay Secure Checkout...`;
                
                const options = {
                    key: data.key_id,
                    amount: data.amount_inr * 100,
                    currency: "INR",
                    name: "SI Filings Pro",
                    description: "Wallet Recharge",
                    order_id: data.razorpay_order_id,
                    handler: async function (response) {
                        statusBox.innerHTML = "⏳ Verifying cryptographic signature...";
                        try {
                            const verifyResp = await fetch(`${CLOUD_API_URL}/api/billing/verify-razorpay`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    order_id: data.order_id,
                                    razorpay_payment_id: response.razorpay_payment_id,
                                    razorpay_order_id: response.razorpay_order_id,
                                    razorpay_signature: response.razorpay_signature
                                })
                            });
                            const vData = await verifyResp.json();
                            if (verifyResp.ok && vData.success) {
                                statusBox.style.background = "rgba(16, 185, 129, 0.12)";
                                statusBox.style.borderColor = "#10b981";
                                statusBox.style.color = "#a7f3d0";
                                statusBox.innerHTML = `✅ <strong>Payment Successful!</strong><br>Added ${vData.credits_added} SI Credits to your firm wallet.`;
                            } else {
                                throw new Error(vData.error || "Signature verification failed");
                            }
                        } catch (e) {
                            statusBox.style.background = "rgba(239, 68, 68, 0.12)";
                            statusBox.style.color = "#fca5a5";
                            statusBox.innerHTML = `❌ Verification failed: ${e.message}`;
                        }
                    },
                    prefill: { email: email },
                    theme: { color: "#38bdf8" }
                };
                
                const rzp = new Razorpay(options);
                rzp.on('payment.failed', function (response){
                    statusBox.style.background = "rgba(239, 68, 68, 0.12)";
                    statusBox.style.color = "#fca5a5";
                    statusBox.innerHTML = `❌ Payment failed: ${response.error.description}`;
                });
                rzp.open();
                statusBox.innerHTML = "Secure Checkout Window Opened.";
            } else if (data.payment_mode === "RAZORPAY_DEV_SIMULATED") {
                statusBox.style.background = "rgba(16, 185, 129, 0.12)";
                statusBox.style.borderColor = "#10b981";
                statusBox.style.color = "#a7f3d0";
                statusBox.innerHTML = `✅ <strong>Dev Simulated Payment Created!</strong><br>Order ID: ${data.order_id}`;
            }
        } else {
            statusBox.style.background = "rgba(239, 68, 68, 0.12)";
            statusBox.style.color = "#fca5a5";
            statusBox.innerHTML = `❌ Error: ${data.error || "Could not generate invoice."}`;
        }
    } catch (err) {
        statusBox.style.background = "rgba(245, 158, 11, 0.12)";
        statusBox.innerHTML = `⚠️ Network communication error with cloud billing server.`;
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "Proceed to Secure Checkout";
    }
}

// ============================================================================
// Helper Functions
// ============================================================================

function copyLicenseKey() {
    const keyVal = document.getElementById("display-license-key").innerText;
    navigator.clipboard.writeText(keyVal);
    alert("Professional License Key copied to clipboard! Paste it into your SI Filings Pro Windows app.");
}
