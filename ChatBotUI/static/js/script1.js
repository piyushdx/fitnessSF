$(function () {
    var owner = $('#owner');
    var cardNumber = $('#cardNumber');
    var cardNumberField = $('#card-number-field');
    var CVV = $("#cvv");
    var mastercard = $("#mastercard");
    var confirmButton = $('#confirm-purchase');
    var visa = $("#visa");
    var amex = $("#amex");

    // Use the payform library to format and validate the payment fields.
    cardNumber.payform('formatCardNumber');
    CVV.payform('formatCardCVC');

    cardNumber.keyup(function () {
        amex.removeClass('transparent');
        visa.removeClass('transparent');
        mastercard.removeClass('transparent');

        if ($.payform.validateCardNumber(cardNumber.val()) == false) {
            cardNumberField.addClass('has-error');
        } else {
            cardNumberField.removeClass('has-error');
            cardNumberField.addClass('has-success');
        }

        if ($.payform.parseCardType(cardNumber.val()) == 'visa') {
            mastercard.addClass('transparent');
            amex.addClass('transparent');
        } else if ($.payform.parseCardType(cardNumber.val()) == 'amex') {
            mastercard.addClass('transparent');
            visa.addClass('transparent');
        } else if ($.payform.parseCardType(cardNumber.val()) == 'mastercard') {
            amex.addClass('transparent');
            visa.addClass('transparent');
        }
    });

    function displayErrorMessage(message, element) {
        // Display the error message above the corresponding input field
        var errorMessage = element.siblings('.error-message');
        errorMessage.text(message);
        errorMessage.show();
        console.log(message);

        element.on('input', function() {
            if (validateInput(element)) {
                errorMessage.hide();
            }
        });
    }
    function validateInput(element) {
        var inputValue = element.val();
      
        // Perform the validation based on the element's ID or other criteria
        if (element.attr('id') === 'owner') {
            // Validation for owner name
            if (!/^[a-zA-Z\s]+$/.test(inputValue)) {
                return false;
            }
            if (inputValue.length < 5) {
                return false;
            }
        } else if (element.attr('id') === 'cardNumber') {
            // Validation for card number
            if (!$.payform.validateCardNumber(inputValue)) {
                return false;
            }
        } else if (element.attr('id') === 'cvv') {
            // Validation for CVV
            if (!validateCVV(inputValue)) {
                return false;
            }
        } else if (element.attr('id') === 'expiration-year') {
            // Validation for expiration year
            if (!validateExpirationDate()) {
                return false;
            }
        }
      
        return true;
    }


    confirmButton.click(function (e) {
        e.preventDefault();

        var isCardValid = $.payform.validateCardNumber(cardNumber.val());
        var isCvvValid = $.payform.validateCardCVC(CVV.val());
        var isExpirationValid = validateExpirationDate();

        if (!/^[a-zA-Z\s]+$/.test(owner.val())) {
            displayErrorMessage("Invalid owner name", owner);
        } else if (owner.val().length < 5) {
            displayErrorMessage("Owner name should be at least 5 characters", owner);
        } else if (!isCardValid) {
            displayErrorMessage("Invalid card number", cardNumber);
        } else if (!isCvvValid) {
            displayErrorMessage("Invalid CVV", CVV);
        } else if (!isExpirationValid) {
            displayErrorMessage("Invalid expiration date", expirationYear);
        } else {
            // Everything is correct. Add your form submission code here.
            displaySuccessMessage("Payment successful");
        }
    });

    function displaySuccessMessage(message) {
        // Display a success message
        alert(message);
    }

    // Restrict input in card holder name field to alphabetic characters and spaces
    owner.keypress(function (event) {
        var inputValue = event.which;
        if (
            !(inputValue >= 65 && inputValue <= 90) && // Uppercase letters
            !(inputValue >= 97 && inputValue <= 122) && // Lowercase letters
            !(inputValue == 32) // Space
        ) {
            event.preventDefault();
        }
    });

    function validateExpirationDate() {
        var selectedMonth = parseInt($('#expiration-date select:first-child').val());
        var selectedYear = parseInt($('#expiration-date select:last-child').val());

        // Get the current date
        var currentDate = new Date();
        var currentYear = currentDate.getFullYear();
        var currentMonth = currentDate.getMonth() + 1; // January is 0, so add 1

        // Validate the expiration date
        if (selectedYear > currentYear) {
            return true;
        } else if (selectedYear === currentYear && selectedMonth >= currentMonth) {
            return true;
        } else {
            return false;
        }
    }
});
