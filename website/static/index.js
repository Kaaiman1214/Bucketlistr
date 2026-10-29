// Edit page: only show the completion date fields while "Completed" is ticked.
document.addEventListener('DOMContentLoaded', function () {
    var checkbox = document.getElementById('completed');
    var fields = document.getElementById('completed-fields');
    if (!checkbox || !fields) return;

    function toggle() {
        fields.style.display = checkbox.checked ? '' : 'none';
    }

    checkbox.addEventListener('change', toggle);
    toggle();
});
