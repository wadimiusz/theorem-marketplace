window.addEventListener('DOMContentLoaded', () => {
    const connectWalletButton = document.getElementById('connectWalletButton');

    // Check if MetaMask is installed
    if (typeof window.ethereum !== 'undefined') {
        console.log('MetaMask is installed!');

        // Function to handle wallet connection
        async function connectWallet() {
            try {
                // Request account access if needed
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                const account = accounts[0];
                console.log('Connected account:', account);

                // Update the button text or display the account
                connectWalletButton.textContent = 'Connected: ' + account.substring(0, 6) + '...' + account.slice(-4);

                // Optionally, store the account information for later use
                // e.g., window.userAccount = account;

                // Disable the button after connection
                connectWalletButton.disabled = true;
            } catch (error) {
                console.error('User rejected the connection request');
            }
        }

        // Attach the event handler
        connectWalletButton.addEventListener('click', connectWallet);
    } else {
        // MetaMask is not installed
        connectWalletButton.textContent = 'Install MetaMask';
        connectWalletButton.onclick = () => {
            window.open('https://metamask.io/download.html', '_blank');
        };
    }
});

// Listen for account changes
window.ethereum.on('accountsChanged', function (accounts) {
    if (accounts.length > 0) {
        const account = accounts[0];
        window.userAccount = account;
        connectWalletButton.textContent = 'Connected: ' + account.substring(0, 6) + '...' + account.slice(-4);
        connectWalletButton.disabled = true;
    } else {
        // No accounts available (user disconnected)
        connectWalletButton.textContent = 'Connect Wallet';
        connectWalletButton.disabled = false;
    }
});

// Listen for network changes (optional)
window.ethereum.on('chainChanged', (chainId) => {
    // Reload the page to avoid any stale data
    window.location.reload();
});

