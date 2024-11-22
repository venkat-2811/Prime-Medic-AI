// Google Translate API Key
const API_KEY = 'YOUR_API_KEY_HERE';

// Function to translate text
async function translateText(text, targetLanguage) {
    const response = await fetch(`https://translation.googleapis.com/language/translate/v2?key=${API_KEY}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            q: text,
            target: targetLanguage,
        }),
    });

    const data = await response.json();
    return data.data.translations[0].translatedText;
}

// Function to translate the entire page
async function translatePage(language) {
    const elements = document.querySelectorAll('[id]'); // Select all elements with an ID
    for (const element of elements) {
        const originalText = element.textContent;
        const translatedText = await translateText(originalText, language);
        element.textContent = translatedText;
    }
}

// Event Listener for Language Selector
document.getElementById('languageSelector').addEventListener('change', (event) => {
    const selectedLanguage = event.target.value;
    translatePage(selectedLanguage);
});
