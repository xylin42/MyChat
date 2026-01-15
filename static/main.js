import './tailwind.css'

import Alpine from 'alpinejs'
import 'htmx.org'
import {putChatsToDB} from "./db"
import {setupUserEvent} from "./userEvent";
import {strictObject} from "./stirctObject";
import {chatStore, friendStore} from "./stores";

function setupMyChat() {
    const constants = strictObject(window.__mychatConstants)
    const userEventTarget = setupUserEvent(constants.userEventUrl)
    userEventTarget.addEventListener(constants.USER_EVENT_NEW_MESSAGE, (e) => {
        console.log('新消息抵达', e)
        const conv = e.payload
        putChatsToDB([conv]).then(txCompleteEvent => {
            console.log(txCompleteEvent)
            chatStore.put(conv)
        })
    })
    return {
        userEventTarget,
        chatStore,
        friendStore,
    }
}

export const mychat = setupMyChat()

window.Alpine = Alpine
window.mychat = mychat

Alpine.start()