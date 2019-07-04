var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host: host,
        old_pwd: '',
        new_pwd: '',
        new_cpwd: '',
        error_opwd: false,
        error_pwd: false,
        error_cpwd: false
    },
    methods: {
        // 检查旧密码
        check_opwd(){
            var re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.old_pwd)) {
                this.error_opwd = false;
            } else {
                this.error_opwd = true;
            }
        },
        // 检查新密码
        check_pwd(){
            var re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.new_pwd)) {
                this.error_pwd = false;
            } else {
                this.error_pwd = true;
            }
        },
        // 检查确认密码
        check_cpwd: function () {
            if (this.new_pwd != this.new_cpwd) {
                this.error_cpwd = true;
            } else {
                this.error_cpwd = false;
            }
        },
        // 提交修改密码
        on_submit: function () {
            this.check_opwd();
            this.check_pwd();
            this.check_cpwd();

            if (this.error_opwd == true || this.error_pwd == true || this.error_cpwd == true) {
                // 不满足修改密码条件：禁用表单
                window.event.returnValue = false
            }
        },
    }
});
