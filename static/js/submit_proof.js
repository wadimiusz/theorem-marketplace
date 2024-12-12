window.addEventListener('DOMContentLoaded', async () => {
    // Check if MetaMask is installed
    if (typeof window.ethereum !== 'undefined') {
        console.log('MetaMask is installed!');
    } else {
        alert('Please install MetaMask to use this feature.');
        return;
    }

    // Get references to form elements
    const submitProofForm = document.getElementById('submitProofForm');
    const statusMessage = document.getElementById('statusMessage');

    // Add event listener to the form submission
    submitProofForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent the default form submission

        // Clear previous status messages and classes
        statusMessage.textContent = '';
        statusMessage.classList.remove('success', 'error');
        statusMessage.style.display = 'none';

        // Get the proof from the form
        const proof = document.getElementById('proof').value.trim();

        // Validate input
        if (!proof) {
            statusMessage.textContent = 'Please enter your proof.';
            statusMessage.classList.add('error');
            statusMessage.style.display = 'block';
            return;
        }

        // Disable the submit button to prevent multiple submissions
        submitProofForm.querySelector('button[type="submit"]').disabled = true;

        // Syntax checking
        statusMessage.textContent = 'Checking proof syntax... Please wait.';
        statusMessage.classList.add('success');
        statusMessage.style.display = 'block';

        try {
            const syntaxCheckResponse = await fetch('/api/check_syntax', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ code: proof })
            });
            const syntaxCheckResult = await syntaxCheckResponse.json();
            console.log(syntaxCheckResult)
            if (!syntaxCheckResult.success) {
                statusMessage.textContent = `Syntax Error: ${syntaxCheckResult.message}`;
                statusMessage.classList.add('error');
                statusMessage.style.display = 'block';
                submitProofForm.querySelector('button[type="submit"]').disabled = false;
                return;
            }
        } catch (error) {
            console.error('Syntax checking error:', error);
            statusMessage.textContent = 'An error occurred during syntax checking.';
            statusMessage.classList.add('error');
            statusMessage.style.display = 'block';
            submitProofForm.querySelector('button[type="submit"]').disabled = false;
            return;
        }

        // Proceed with transaction
        statusMessage.textContent = 'Syntax check passed. Sending transaction...';
        statusMessage.classList.add('success');
        statusMessage.style.display = 'block';

        try {
            // Request account access if needed
            await window.ethereum.request({ method: 'eth_requestAccounts' });

            // Instantiate provider and signer
            const provider = new ethers.providers.Web3Provider(window.ethereum);
            const signer = provider.getSigner();

            // Instantiate the contract
            const contract = new ethers.Contract(contractAddress, contractABI, signer);

            // Send the transaction
            const tx = await contract.requestBounty(theorem, proof);
            let txHash = tx.hash;

            const etherscanBaseUrl = 'https://sepolia.etherscan.io/tx/';
            let etherscanLink = `${etherscanBaseUrl}${txHash}`;
            statusMessage.innerHTML = `Transaction submitted. <a href="${etherscanLink}" target="_blank">View on Etherscan</a>. Waiting for confirmation...`;
            statusMessage.classList.add('success');
            statusMessage.style.display = 'block';

            // Wait for transaction to be mined
            try {
                const receipt = await tx.wait();

                // Check if the transaction was successful
                if (receipt.status === 1) {
                    statusMessage.innerHTML = `Proof submitted successfully! <a href="${etherscanLink}" target="_blank">View on Etherscan</a>.`;
                    statusMessage.classList.add('success');
                    statusMessage.style.display = 'block';

                    // Optionally, clear the form or perform other actions
                    submitProofForm.reset();
                } else {
                    statusMessage.textContent = 'Transaction failed.';
                    statusMessage.classList.add('error');
                    statusMessage.style.display = 'block';
                }
            } catch (error) {
                if (error.code === ethers.errors.TRANSACTION_REPLACED) {
                    if (error.cancelled) {
                        statusMessage.textContent = 'Transaction was cancelled.';
                        statusMessage.classList.add('error');
                        statusMessage.style.display = 'block';
                    } else {
                        // Transaction was replaced
                        const replacementTx = error.replacement;
                        txHash = replacementTx.hash;
                        etherscanLink = `${etherscanBaseUrl}${txHash}`;

                        // Update status message
                        statusMessage.innerHTML = `Transaction replaced. <a href="${etherscanLink}" target="_blank">View on Etherscan</a>. Waiting for confirmation...`;
                        statusMessage.classList.add('success');
                        statusMessage.style.display = 'block';

                        // Get the receipt of the replacement transaction
                        const replacementReceipt = error.receipt;
                        if (replacementReceipt && replacementReceipt.status === 1) {
                            statusMessage.innerHTML = `Proof submitted successfully! (Transaction replaced) <a href="${etherscanLink}" target="_blank">View on Etherscan</a>`;
                            statusMessage.classList.add('success');
                            statusMessage.style.display = 'block';

                            // Optionally, clear the form or perform other actions
                            submitProofForm.reset();
                        } else {
                            statusMessage.textContent = 'Replacement transaction failed.';
                            statusMessage.classList.add('error');
                            statusMessage.style.display = 'block';
                        }
                    }
                } else {
                    throw error; // Rethrow error to be caught by the outer catch block
                }
            }
        } catch (error) {
            console.error('Error:', error);

            if (error.code === 4001) {
                // User rejected transaction
                statusMessage.textContent = 'Transaction rejected by user.';
            } else {
                statusMessage.textContent = 'An error occurred. See console for details.';
            }
            statusMessage.classList.add('error');
            statusMessage.style.display = 'block';
        } finally {
            // Re-enable the submit button
            submitProofForm.querySelector('button[type="submit"]').disabled = false;
        }
    });
});