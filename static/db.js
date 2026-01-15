const dbName = 'mychat'
const friendStoreName = 'friends'
const conversationStoreName = 'conversations'

let dbPromise = null

export async function putFriendsToDB(friends) {
    return putObjectsToDB(friendStoreName, friends)
}

export async function putChatsToDB(chats) {
    return putObjectsToDB(conversationStoreName, chats)
}

export async function putObjectsToDB(storeName, objects) {
    const db = await getDB()
    const tx = db.transaction(storeName, 'readwrite')
    const store = tx.objectStore(storeName)
    for (const object of objects) {
        store.put(object)
    }
    return new Promise((resolve, reject)=>{
        tx.oncomplete = (event) => {
            resolve(event)
        }
        tx.onerror = (event) => {
            reject(event)
        }
    })
}

function getDB() {
    if (!dbPromise) {
        dbPromise = openDB()
    }
    return dbPromise
}

export function deleteDB() {
    return new Promise((resolve, reject) => {
        const req = indexedDB.deleteDatabase(dbName)

        req.onerror = (event) => {
            reject(event)
        }

        req.onsuccess = (event) => {
            resolve()
        }
    })
}

function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(dbName, 1)
        request.onupgradeneeded = (event) => {
            const db = event.target.result
            if (event.oldVersion < 1) {
                db.createObjectStore('friends', {
                    keyPath: 'id',
                    autoIncrement: true,
                })
                db.createObjectStore('conversations', {
                    keyPath: 'conv_id',
                    autoIncrement: true,
                })
            }
        }

        request.onsuccess = (event) => {
            const db = event.target.result

            db.onversionchange = () => {
                db.close()
                dbPromise = null
                console.warn('数据库版本变化，已关闭旧连接')
            }

            resolve(db)
        }

        request.onerror = () => {
            reject(request.error)
        }
    })
}