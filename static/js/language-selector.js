const languageButton = document.getElementById('language-button');
const languageDropdown = document.getElementById('language-dropdown-menu');
const languageOptions = languageDropdown.querySelectorAll('a');


const languageDropdownFlowbite = new Dropdown(languageDropdown, languageButton);


function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}

// Function to get a cookie
function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

function removeLangQueryParam() {
    const url = new URL(window.location.href);
    url.searchParams.delete('lang');
    window.history.replaceState({}, '', url);
}



// Handle language selection
languageOptions.forEach(option => {
    option.addEventListener('click', function(e) {
        e.preventDefault();

        console.log('Language selected:', this.getAttribute('data-lang'));
        

        setCookie('lang', this.getAttribute('data-lang'), 365);

        removeLangQueryParam();

        languageDropdownFlowbite.hide();
        window.location.reload();

    });
});