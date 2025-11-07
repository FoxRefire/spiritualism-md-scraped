const inputText = document.getElementById('inputText');
const sendButton = document.getElementById('send');

// Function to check if input is empty and update button state
function updateButtonState() {
    const text = inputText.value.trim();
    sendButton.disabled = text === '';
}

// Function to send the query
async function sendQuery() {
    const text = inputText.value.trim();
    if (text === '') {
        return;
    }

    const systemPrompt = "このリポジトリ内のスピリチュアリズム関連文献を参照してユーザーの質問に回答してください";
    const repoName = "FoxRefire/spiritualism-md-scraped";
    const guid = crypto.randomUUID();

    const requestBody = {
        "engine_id":"multihop",
        "user_query":`<relevant_context>${systemPrompt}</relevant_context>${text}`,
        "keywords":[],
        "repo_names":[repoName],
        "additional_context":"",
        "query_id":`_${guid}`,
        "use_notes":false,
        "generate_summary":false
    }
    
    window.open(`https://deepwiki.com/search/_${guid}`, "_blank");
    await fetch("https://corsproxy.io/?url=https://api.devin.ai/ada/query", {
        "credentials": "omit",
        "headers": {
            "content-type": "application/json",
        },
        "body": JSON.stringify(requestBody),
        "method": "POST",
        "mode": "cors"
    });
}

// Button click event
sendButton.addEventListener('click', sendQuery);

// Enter key to send (Shift+Enter for new line)
inputText.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuery();
    }
});

// Update button state on input change
inputText.addEventListener('input', updateButtonState);

// Initial button state check
updateButtonState();