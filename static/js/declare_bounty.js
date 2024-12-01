window.addEventListener('DOMContentLoaded', async () => {
    // Check if MetaMask is installed
    if (typeof window.ethereum !== 'undefined') {
        console.log('MetaMask is installed!');
    } else {
        alert('Please install MetaMask to use this feature.');
        return;
    }

    // Get references to form elements
    const declareBountyForm = document.getElementById('declareBountyForm');
    const statusMessage = document.getElementById('statusMessage');

    // Add event listener to the form submission
    declareBountyForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent the default form submission

        // Clear previous status messages and classes
        statusMessage.textContent = '';
        statusMessage.classList.remove('success', 'error');
        statusMessage.style.display = 'none';

        // Get form values
        const theorem = document.getElementById('theorem').value.trim();
        const bountyAmount = document.getElementById('bounty_amount').value.trim();

        // Validate inputs
        if (!theorem || !bountyAmount) {
            statusMessage.textContent = 'Please fill out all fields.';
            statusMessage.classList.add('error');
            statusMessage.style.display = 'block';
            return;
        }

        // Disable the submit button to prevent multiple submissions
        declareBountyForm.querySelector('button[type="submit"]').disabled = true;

        statusMessage.textContent = 'Checking theorem syntax... Please wait.';
        statusMessage.style.display = 'block';

        try {
            // Syntax checking
            const syntaxCheckResponse = await fetch('/api/check_syntax', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ code: theorem })
            });
            const syntaxCheckResult = await syntaxCheckResponse.json();

            if (!syntaxCheckResult.success) {
                statusMessage.textContent = `Syntax Error: ${syntaxCheckResult.message}`;
                statusMessage.classList.add('error');
                statusMessage.style.display = 'block';
                declareBountyForm.querySelector('button[type="submit"]').disabled = false;
                return;
            }
        } catch (error) {
            console.error('Syntax checking error:', error);
            statusMessage.textContent = 'An error occurred during syntax checking.';
            statusMessage.classList.add('error');
            statusMessage.style.display = 'block';
            declareBountyForm.querySelector('button[type="submit"]').disabled = false;
            return;
        }

        // Proceed with transaction
        statusMessage.textContent = 'Syntax check passed. Sending transaction...';
        statusMessage.classList.add('success');
        statusMessage.style.display = 'block';

        try {
            // Convert bounty amount to Wei (smallest unit of Ether)
            const bountyAmountWei = ethers.utils.parseEther(bountyAmount);

            // Request account access if needed
            await window.ethereum.request({ method: 'eth_requestAccounts' });
            const provider = new ethers.providers.Web3Provider(window.ethereum);
            const signer = provider.getSigner();

            // Instantiate the contract
            const contract = new ethers.Contract(contractAddress, contractABI, signer);

            // Send the transaction
            const tx = await contract.declareBounty(theorem, {
                value: bountyAmountWei
            });

            let txHash = tx.hash;
            const etherscanBaseUrl = 'https://sepolia.etherscan.io/tx/';
            let etherscanLink = `${etherscanBaseUrl}${txHash}`;

            // Update status message with the link
            statusMessage.innerHTML = `Transaction submitted. <a href="${etherscanLink}" target="_blank">View on Etherscan</a>. Waiting for confirmation...`;
            statusMessage.classList.add('success');
            statusMessage.style.display = 'block';

            // Wait for transaction to be mined
            let receipt;

            try {
                receipt = await tx.wait();

                if (receipt.status === 1) {
                    statusMessage.innerHTML = `Bounty declared successfully! <a href="${etherscanLink}" target="_blank">View on Etherscan</a>.`;
                    statusMessage.classList.add('success');
                    statusMessage.style.display = 'block';

                    // Prepare data to send to the backend
                    const data = {
                        theorem: theorem,
                        bounty_amount: bountyAmount,
                        transaction_hash: receipt.transactionHash,
                        user_address: await signer.getAddress()
                    };

                    // Send the data to the backend
                    sendBountyToBackend(data);

                    // Optionally reset the form
                    declareBountyForm.reset();
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
                            statusMessage.innerHTML = `Bounty declared successfully! (Transaction replaced) <a href="${etherscanLink}" target="_blank">View on Etherscan</a>.`;
                            statusMessage.classList.add('success');
                            statusMessage.style.display = 'block';

                            // Prepare data to send to the backend
                            const data = {
                                theorem: theorem,
                                bounty_amount: bountyAmount,
                                transaction_hash: replacementReceipt.transactionHash,
                                user_address: await signer.getAddress()
                            };

                            // Send the data to the backend
                            sendBountyToBackend(data);

                            // Optionally reset the form
                            declareBountyForm.reset();
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
            declareBountyForm.querySelector('button[type="submit"]').disabled = false;
        }
    });

    // Function to send bounty data to the backend
    function sendBountyToBackend(data) {
        fetch('/api/add_bounty', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
            .then(response => {
                if (response.ok) {
                    console.log('Bounty added to the database.');
                    // Optionally redirect to the bounties list
                    // window.location.href = '/bounties';
                } else {
                    statusMessage.textContent = 'Failed to add bounty to the database.';
                    statusMessage.classList.add('error');
                    statusMessage.style.display = 'block';
                    console.error('Server responded with status:', response.status);
                }
            })
            .catch(error => {
                statusMessage.textContent = 'An error occurred while updating the database.';
                statusMessage.classList.add('error');
                statusMessage.style.display = 'block';
                console.error('Error:', error);
            });
    }

});