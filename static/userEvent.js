let timer = null
const timeout = 3000

function scheduleTimer(userEvent) {
    if (timer !== null) {
        clearTimeout(timer)
    }
    timer = setTimeout(()=>{
        console.log("userEvent断线")
        const event = new UserEvent('offline')
        userEvent.dispatchEvent(event)
    }, 3000)
}

class UserEvent extends Event {
    constructor(type, payload) {
        super(type)
        this.payload = payload
    }
}

class UserEventTarget extends EventTarget {
    constructor(es) {
        super()
        this.es = es
    }
}

export function setupUserEvent(eventUrl) {
    const es = new EventSource(eventUrl)
    const userEventTarget = new UserEventTarget(es)
    es.addEventListener('keep-alive', ()=>{
        scheduleTimer(userEventTarget)
    })
    es.onmessage = (e) => {
        const data = JSON.parse(e.data)
        const type = data.type
        const ue = new UserEvent(type, data.payload)
        console.log('新消息抵达', ue)
        userEventTarget.dispatchEvent(ue)
    }
    return userEventTarget
}
