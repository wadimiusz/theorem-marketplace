document.addEventListener('DOMContentLoaded', async function() {
    const connectWalletButton = document.getElementById('connectWalletForContact');
    const contactForm = document.getElementById('contactForm');
    const walletConnectionRequired = document.getElementById('walletConnectionRequired');
    const contactFormContainer = document.getElementById('contactFormContainer');
    const userWalletAddress = document.getElementById('userWalletAddress');
    const statusMessage = document.getElementById('statusMessage');

    // Check if wallet is already connected (from global state)
    if (window.ethereum && window.ethereum.selectedAddress) {
        showContactForm(window.ethereum.selectedAddress);
    }

    // Handle wallet connection button
    connectWalletButton.addEventListener('click', async function() {
        try {
            if (!window.ethereum) {
                throw new Error("No Ethereum wallet found. Please install MetaMask or another wallet provider.");
            }

            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            const account = accounts[0];
            
            showContactForm(account);
        } catch (error) {
            console.error("Error connecting wallet:", error);
            displayStatus(`Error: ${error.message}`, 'error');
        }
    });

    // Listen for account changes
    if (window.ethereum) {
        window.ethereum.on('accountsChanged', function (accounts) {
            if (accounts.length > 0) {
                showContactForm(accounts[0]);
            } else {
                hideContactForm();
            }
        });
    }

    // Handle form submission
    contactForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        if (!window.ethereum || !window.ethereum.selectedAddress) {
            displayStatus("Please connect your wallet first.", 'error');
            return;
        }

        const subject = document.getElementById('subject').value;
        const message = document.getElementById('message').value;
        const walletAddress = window.ethereum.selectedAddress;
        const timestamp = Date.now().toString();

        // Get a signature to verify ownership of the wallet
        try {
            // Create a message with timestamp that will be verified on the server
            const messageToSign = `Contact Form Submission\nWallet: ${walletAddress}\nTimestamp: ${timestamp}`;
            
            const signature = await signMessage(walletAddress, messageToSign);
            
            // Submit the contact form data
            const response = await fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    subject,
                    message,
                    walletAddress,
                    signature,
                    timestamp // Include timestamp for verification
                }),
            });

            const data = await response.json();
            
            if (response.ok) {
                displayStatus("Your message has been sent successfully!", 'success');
                contactForm.reset();
            } else {
                displayStatus(`Error: ${data.error || 'Failed to send message'}`, 'error');
            }
        } catch (error) {
            console.error("Error submitting form:", error);
            displayStatus(`Error: ${error.message}`, 'error');
        }
    });

    // Function to sign a message with the wallet
    async function signMessage(address, message) {
        try {
            const signature = await window.ethereum.request({
                method: 'personal_sign',
                params: [message, address]
            });
            return signature;
        } catch (error) {
            console.error("Error signing message:", error);
            throw new Error("Failed to sign message with wallet. Please try again.");
        }
    }

    // Helper function to show the contact form
    function showContactForm(address) {
        walletConnectionRequired.style.display = 'none';
        contactFormContainer.style.display = 'block';
        userWalletAddress.textContent = address;
    }

    // Helper function to hide the contact form
    function hideContactForm() {
        walletConnectionRequired.style.display = 'block';
        contactFormContainer.style.display = 'none';
        userWalletAddress.textContent = '';
    }

    // Helper function to display status messages
    function displayStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = type;
        statusMessage.style.display = 'block';

        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                statusMessage.style.display = 'none';
            }, 5000);
        }
    }
}); 