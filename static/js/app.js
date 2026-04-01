function load_create_form(element, data) {
    const get_url = data.create_form_url;
    data.createButton = element;
    fetch(get_url).then((response) => {
        if(!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        response.text().then((othertext) => element.outerHTML = othertext)});
};
window.load_create_form = load_create_form;
function load_target_url(element, target) {
    fetch(target).then((response) => {
        if(!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        response.text()
            .then((othertext) => element.innerHTML = othertext)
    });
};
window.load_target_url = load_target_url;
function editable_text(element, key) {
    element.outerHTML = '<input x-model="'+key+'" type="text" @keydown.enter="update = true"/>';
};
window.editable_text = editable_text;
