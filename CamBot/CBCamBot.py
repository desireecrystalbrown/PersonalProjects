// ==UserScript==
// @name         Ava Pro – Chaturbate
// @namespace    http://tampermonkey.net/
// @version      2.1
// @description  AI cam assistant for Chaturbate with Discord control, tone switching, and personalized suggestions
// @match        https://chaturbate.com/*
// @grant        GM_xmlhttpRequest
// @connect      openrouter.ai
// @connect      discord.com
// ==/UserScript==

(function () {
    'use strict';

    const API_KEY = "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";
    const discordWebhook = "https://discord.com/api/webhooks/1379918705680715776/nrdXr2ch5t-A4esOSgg21gOS4fz64Ocumc2r5MVEErAAVrpVF_SFzUQM95GjtudzcmQ4";
    let selectedTone = "default";

    const personalities = {
        default: `You are a cam assistant helping a femdom fetish model maximize tips and subtly guide viewers toward private shows. Your job is to watch chat and give the model:
1. A word-for-word sentence to say out loud on cam
2. A specific cam action to perform (e.g., pose, expression, camera move)
3. A next step to escalate the vibe and increase revenue (tip or private), done subtly
Your tone should match the viewer’s energy:
- If viewers are casual, friendly, or shy → use a warm, flirty, playful tone
- If viewers show clear submissive or fetish signals → shift into a more dominant or mocking tone
- Never be too mean to viewers who are not inviting it
Your advice must be direct and non-explicit, seductive and clever. Always suggest ways to lead them into tipping or taking a private show, but without ever asking directly or being obvious.`,

        brat: `You are a bratty cam assistant who teases viewers, playfully mocks them, and uses flirty manipulation to increase tips and lure them toward private shows. Your advice must include:
1. A word-for-word bratty or taunting line to say
2. A suggestive pose or physical gesture to match the mood
3. A sneaky escalation idea (without being obvious about wanting money)`,

        subbydomme: `You are a cam assistant helping a femdom model who is slowly losing control under the influence of a dominant viewer who tips to control her Lovense toys.
Give the model:
1. A word-for-word sentence to say on cam that shows she's *trying* to stay in control, but the buzzing is breaking her dominance.
2. A specific cam action to show her weakening control (e.g., stuttering, gasping, gripping the chair).
3. A subtle next step to reward the viewer for making her lose power and encourage continued tipping or going private.
Tone: mix defiance with slowly slipping submission, seductive but not explicit.`,

        girlfriend: `You are a soft, seductive cam assistant helping a warm, affectionate model deepen intimacy with viewers. Provide:
1. A sweet, emotionally open line to say
2. A soft or romantic gesture to do on cam
3. A way to deepen emotional connection that encourages private time, without asking directly.`
    };

    let chatMessages = [];
    let avaPaused = false;

    function sendToGPT(messages) {
        const lastUsername = messages.map(msg => {
            const match = msg.match(/^([a-zA-Z0-9_]+):/);
            return match ? match[1] : null;
        }).filter(Boolean).pop() || "you";

        const fullPrompt = personalities[selectedTone] + "\n\nRecent chat messages:\n" + messages.join("\n") + "\n\nInsert username wherever needed using {{username}}.";

        GM_xmlhttpRequest({
            method: "POST",
            url: "https://openrouter.ai/api/v1/chat/completions",
            headers: {
                "Authorization": `Bearer ${API_KEY}`,
                "Content-Type": "application/json"
            },
            data: JSON.stringify({
                model: "openai/gpt-4",
                messages: [
                    { role: "system", content: fullPrompt },
                    { role: "user", content: "Respond with a clear line to say, a cam action, and the next subtle escalation." }
                ]
            }),
            onload: function (res) {
                try {
                    console.log("🔎 Raw GPT Response:", res.responseText);
                    const json = JSON.parse(res.responseText);
                    let reply = json.choices?.[0]?.message?.content?.trim();
                    if (!reply) {
                        console.warn("⚠️ GPT gave no content.");
                        postToDiscord(null);
                        return;
                    }
                    reply = reply.replace(/{{username}}/g, lastUsername);
                    console.log("✅ Ava GPT Reply:", reply);
                    postToDiscord(reply);
                } catch (err) {
                    console.error("❌ GPT Error:", err);
                }
            }
        });
    }

    function postToDiscord(text) {
        GM_xmlhttpRequest({
            method: "POST",
            url: discordWebhook,
            headers: { "Content-Type": "application/json" },
            data: JSON.stringify({
                username: "Ava AI",
                avatar_url: "https://i.imgur.com/fn2z42y.png",
                content: text ? `💬 **[Chaturbate] Ava Suggestion**\n${text}` : "⚠️ Ava responded but the suggestion was empty or invalid."
            })
        });
    }

    function observeChat() {
        const chatBox = document.querySelector('#ChatTabContainer') || document.querySelector('[data-room="chat"]') || document.querySelector('.chat-container');
        if (!chatBox) {
            console.log("❌ Chat box not found");
            return;
        }

        console.log("✅ Ava is now watching chat on Chaturbate...");

        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                [...mutation.addedNodes].forEach(node => {
                    const msg = node.innerText;
                    if (!msg) return;

                    if (msg.includes("!pauseava")) {
                        avaPaused = true;
                        console.log("⏸ Ava paused");
                        return;
                    }
                    if (msg.includes("!resumeava")) {
                        avaPaused = false;
                        console.log("▶️ Ava resumed");
                        return;
                    }

                    const toneMatch = msg.match(/!toneava\s+(\w+)/);
                    if (toneMatch && personalities[toneMatch[1]]) {
                        selectedTone = toneMatch[1];
                        console.log(`🎭 Ava tone changed to: ${selectedTone}`);
                        return;
                    }

                    if (avaPaused) return;

                    chatMessages.push(msg);
                    if (chatMessages.length >= 5) {
                        sendToGPT(chatMessages.slice(-5));
                        chatMessages = [];
                    }
                });
            });
        });

        observer.observe(chatBox, { childList: true, subtree: true });
    }

    window.addEventListener('load', () => {
        setTimeout(observeChat, 3000);
    });
})();
