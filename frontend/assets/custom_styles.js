
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        apply_custom_styles: function(styles) {
            Object.entries(styles).forEach(([selector, properties]) => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    Object.entries(properties).forEach(([property, value]) => {
                        el.style[property] = value;
                    });
                });
            });
            return styles;
        }
    }
});
