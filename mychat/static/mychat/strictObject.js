function strictObject (obj, name = "object") {
  return new Proxy(obj, {
    get(target, prop, receiver) {
      if (!(prop in target)) {
        throw new ReferenceError(
          `${name}: property "${String(prop)}" does not exist`
        );
      }
      return Reflect.get(target, prop, receiver);
    }
  });
}

function alpineRun(func) {
    if (typeof Alpine !== 'undefined') {

        func()
    } else {
        window.addEventListener('alpine:init', func)
    }
}