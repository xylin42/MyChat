import {RecentChatList} from "./recentChatList";
import {deleteDB, putChatsToDB, putFriendsToDB} from "./db";
import Alpine from "alpinejs";

async function loadFull() {
    await deleteDB()

    const friends = JSON.parse(document.getElementById('friends').textContent)
    const states = JSON.parse(document.getElementById('states').textContent)

    friendStore.setFriends(friends)
    chatStore.rebuildFrom(states)

    putFriendsToDB(friends)
    putChatsToDB(states)
}

function setupChatStore() {
    const chatStoreName = 'chats'
    Alpine.store(chatStoreName, {
        manager: null,
        conversations: [],
        totalUnread: null,
        init() {
            console.log("[*] chatStore初始化")
            this.manager = new RecentChatList("conv_id")
            this.refresh()
        },
        loadFull,
        put(conv) {
            this.manager.upsertToFront(conv)
            this.refresh()
        },
        refresh() {
            this.conversations = this.manager.toArray()
            this.totalUnread = this.conversations.reduce((acc, cur) => acc + cur.unread, 0)
        },
        rebuildFrom(states) {
            this.manager.rebuildFromSortedArray(states)
            this.refresh()
        }
    })
    return Alpine.store(chatStoreName)
}

function setupFriendStore(alpine) {
    const friendStoreName = 'friends'
    Alpine.store(friendStoreName, {
        friends: {},
        setFriends(data) {
            for (const item of data) {
                this.friends[item.id] = item
            }
        },
        getFriend(id) {
            return this.friends[id]
        }
    })
    return Alpine.store(friendStoreName)
}

export const chatStore = setupChatStore()
export const friendStore = setupFriendStore()
