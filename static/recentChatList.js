export class RecentChatList {
    constructor(idPath=null) {
        this.head = new Node('__HEAD__', null)
        this.tail = new Node('__TAIL__', null)
        this.idPath = idPath

        this.reset()
    }

    getNode(item) {
        const itemId = item[this.idPath]
        return this.map.get(itemId)
    }

    createNode(item) {
        const itemId = item[this.idPath]
        const node = new Node(itemId, {...item})
        this.map.set(itemId, node)
        return node
    }

    reset() {
        this.map = new Map()
        this.head.next = this.tail
        this.tail.prev = this.head
        this.size = 0
    }

    getItemId(item) {
        return item[this.idPath]
    }

    rebuildFromSortedArray(array) {
        this.reset()

        let prev = this.head

        for (const item of array) {
            const node = this.createNode(item)
            node.prev = prev
            prev.next = node
            prev = node
            this.size++
        }

        prev.next = this.tail
        this.tail.prev = prev
    }

    toArray(limit = Infinity) {
        const res = []
        let cur = this.head.next
        while (cur !== this.tail && res.length < limit) {
            res.push({...cur.data})
            cur = cur.next
        }
        return res
    }

    _remove(node) {
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = null
        node.next = null
    }

    _addToFront(node) {
        node.next = this.head.next
        node.prev = this.head
        this.head.next.prev = node
        this.head.next = node
    }

    upsertToFront(item) {
        let node = this.getNode(item)

        if (!node) {
            node = this.createNode(item)
            this._addToFront(node)
            this.size++
            return
        }

        node.data = {...node.data, ...item}
        this._remove(node)
        this._addToFront(node)
    }
}

class Node {
    constructor(id, data) {
        this.id = id
        this.data = data
        this.prev = null
        this.next = null
    }
}