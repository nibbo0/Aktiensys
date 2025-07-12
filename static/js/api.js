function deepCompare(old, cur) {
    if (typeof old !== typeof cur) {
        // type mismatch
        if (cur === undefined) {
            return { type: 'unset' };
        } else if (old === undefined) {
            return { type: 'set', val: cur };
        } else {
            return { type: 'retyped', change: [typeof old, typeof cur] };
        }
    } else if (Object(old) !== old) {
        // old is not an object
        if (old !== cur) {
            return { type: 'replaced', val: [old, cur] };
        } else {
            return { type: 'unchanged' };
        }
    } else if (Array.isArray(old)) {
        // old is an object, specifically an array
        let [sharedEntries, addedEntries] = cur.reduce((acc, a) => {
            if (old.some(b => deepCompare(a, b).type === 'unchanged')) {
                acc[0].push(a);
            } else {
                acc[1].push(a);
            }
            return acc;
        }, [[], []]);
        // let deletedEntries = old.filter(e => sharedEntries.includes(e));
        // let addedEntries = cur.filter(e => !sharedEntries.includes(e));

        // TODO find a good way of detecting pushes / pops
        // HACK: assume (one deletion and) one insertion is (pop +) push
        if (/* deletedEntries.length === 1 && */ addedEntries.length === 1) {
            return { type: 'appended', val: addedEntries[0] };
        }
    }
    let sharedKeys = Object.keys(old).filter(k => cur.hasOwnProperty(k));
    let deletedKeys = Object.keys(old).filter(k => !sharedKeys.includes(k));
    let addedKeys = Object.keys(cur).filter(k => !sharedKeys.includes(k));
    let changes = [
        ...deletedKeys.map(k => ({ type: 'deleted', key: k, val: old[k] })),
        ...sharedKeys.map(k => ({
            type: 'updated', key: k, val: cur[k],
            diff: deepCompare(old[k], cur[k])
        })).filter(({key, diff}) => diff.type !== 'unchanged'),
        ...addedKeys.map(k => ({ type: 'added', key: k, val: cur[k] }))
    ];
    if (changes.length === 0) {
        return { type: 'unchanged' };
    }
    return { type: 'changed', changes: changes };
}

class ApiValue extends EventTarget {
    #value;

    constructor() {
        super();
    }

    #emitChangeEvent(diff = undefined) {
        let detail = {
            value: this.#value,
        };
        if (diff !== undefined) {
            detail.diff = diff;
        }
        this.dispatchEvent(new CustomEvent("valuechange", { detail: detail }));
    }

    /**
     * Return true if the value is synchronized with the server (polling / sse
     * listen is active).
     */
    get is_running() {
        throw Error("Base class isn't implemented");
    }

    get value() {
        if (!this.is_running) {
            throw new Error(
                "Cannot access unsynchronized value. Try starting synchronization via"
                + " the appropriate subclass function (e.g. `start()`).");
        } else {
            return this.#value;
        }
    }

    tryUpdateValue(updated) {
        if (!this.is_running) {
            throw new Error(
                "Cannot update unsynchronized value. This function should only be called"
                + " from a subclass while it is running.");
        }
        let diff = deepCompare(this.#value, updated);
        if (Object(diff) !== diff || !diff.hasOwnProperty('type')) {
            throw Error(`Invalid diff result: ${JSON.stringify(diff)}`);
        }
        if (diff.type === 'unchanged') {
            return;
        }
        let old = this.#value;
        this.#value = updated;
        this.#emitChangeEvent(diff);
    }
}

class PollingValue extends ApiValue {
    delay;
    #interval;
    #errHandler;

    #server;
    #format;
    #params;
    #options;

    constructor(server, format, params, options = {},
                pollErrHandler = (e) => { throw e; }, interval = 5000) {
        super();
        this.delay = interval;
        this.#interval = undefined;
        this.#errHandler = pollErrHandler;

        this.#server = server;
        this.#format = format;
        this.#params = params;
        this.#options = options;
    }

    start() {
        if (!this.#interval) {
            this.#interval = setInterval(this.#refreshValue.bind(this), this.delay);
        }
    }

    stop() {
        if (this.#interval) {
            clearInterval(this.#interval);
            this.#interval = undefined;
        }
    }

    get is_running() {
        return this.#interval !== undefined;
    }

    poll() {
        return this.#refreshValue().then(() => this.value);
    }

    async #refreshValue() {
        try {
            let updated = await fetch(this.#server + this.#format(this.#params),
                                      this.#options)
                .then(res => res.json())
                .catch(this.#errHandler);
            this.tryUpdateValue(await updated);
        } catch (e) {
            this.dispatchEvent(new CustomEvent("pollErr", { detail: e }));
            console.error("Stopped polling:");
            console.error(e);
            this.stop();
        }
    }
}
