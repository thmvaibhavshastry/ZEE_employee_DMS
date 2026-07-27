$(document).ready(function() {

    $('.alert').delay(4000).fadeOut('slow');

    $('#sidebarToggle').click(function(e) {
        e.preventDefault();
        $('#sidebar').toggleClass('collapsed');
        $('body').toggleClass('sidebar-collapsed');
    });

    $('form').on('submit', function() {
        const btn = $(this).find('button[type="submit"]');
        if (btn.length && !btn.hasClass('no-loading')) {
            btn.prop('disabled', true);
            btn.html('<span class="spinner-border spinner-border-sm me-1"></span> Processing...');
        }
    });

    $('.table').on('init.dt', function() {
        $(this).removeClass('dataTable_no_init');
    });

    $('[data-bs-toggle="tooltip"]').tooltip();

    $('.stat-card, .kpi-card').on('click', function() {
        const link = $(this).data('href');
        if (link) window.location.href = link;
    });
});
