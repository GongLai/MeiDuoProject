var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
        is_show_edit: false,
        provinces: [],
        cities: [],
        districts: [],
        form_address: {
            title: '',
            receiver: '',
            province_id: '',
            city_id: '',
            district_id: '',
            place: '',
            mobile: '',
            tel: '',
            email: '',
        },
        error_receiver: false,
        error_place: false,
        error_mobile: false,
        error_tel: false,
        error_email: false,
        addresses: [],
        editing_address_index: '',
        default_address_id: '',
        edit_title_index: '',
        input_title: '',
        add_title: '新  增',
    },
    mounted() {
        // 获取省份数据
        this.get_provinces();
        // 将用户地址列表绑定到变量, addresses 是django模板传给vue的json字符串
        this.addresses = JSON.parse(JSON.stringify(addresses));
        // 默认地址id
        this.default_address_id = default_address_id;
    },
    watch: {
        // 监听到省份id变化
        'form_address.province_id': function () {
            if (this.form_address.province_id) {
                var url = this.host + '/areas/?area_id=' + this.form_address.province_id;
                axios.get(url, {
                    responseType: 'json'
                })
                    .then(response => {
                        if (response.data.code == '0') {
                            this.cities = response.data.sub_data.subs;
                        } else {
                            console.log(response.data);
                            this.cities = [];
                        }
                    })
                    .catch(error => {
                        console.log(error.response);
                        this.cities = [];
                    });
            }
        },
        // 监听到城市id变化
        'form_address.city_id': function () {
            if (this.form_address.city_id) {
                var url = this.host + '/areas/?area_id=' + this.form_address.city_id;
                axios.get(url, {
                    responseType: 'json'
                })
                    .then(response => {
                        if (response.data.code == '0') {
                            this.districts = response.data.sub_data.subs;
                        } else {
                            console.log(response.data);
                            this.districts = [];
                        }
                    })
                    .catch(error => {
                        console.log(error.response);
                        this.districts = [];
                    });
            }
        }
    },
    methods: {
        // 获取省份数据
        get_provinces() {
            var url = this.host + '/areas/';
            axios.get(url, {
                responseType: 'json'
            })
                .then(response => {
                    if (response.data.code == '0') {
                        this.provinces = response.data.province_list;
                    } else {
                        console.log(response.data);
                        this.provinces = [];
                    }
                })
                .catch(error => {
                    console.log(error.response);
                    this.provinces = [];
                });
        },
        check_receiver() {
            if (!this.form_address.receiver) {
                this.error_receiver = true;
            } else {
                this.error_receiver = false;
            }
        },
        check_place() {
            if (!this.form_address.place) {
                this.error_place = true;
            } else {
                this.error_place = false;
            }
        },
        check_mobile() {
            var re = /^1[345789]\d{9}$/;
            if (re.test(this.form_address.mobile)) {
                this.error_mobile = false;
            } else {
                this.error_mobile = true;
            }
        },
        check_tel() {
            if (this.form_address.tel) {
                var re = /^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$/;
                if (re.test(this.form_address.tel)) {
                    this.error_tel = false;
                } else {
                    this.error_tel = true;
                }
            } else {
                this.error_tel = false;
            }
        },
        check_email() {
            if (this.form_address.email) {
                var re = /^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$/;
                if (re.test(this.form_address.email)) {
                    this.error_email = false;
                } else {
                    this.error_email = true;
                }
            } else {
                this.error_email = false;
            }
        },
        // 清空错误提示信息
        clear_all_errors() {
            this.error_receiver = false;
            this.error_mobile = false;
            this.error_place = false;
            this.error_tel = false;
            this.error_email = false;
        },
        // 展示新增地址弹框时
        show_add_site() {
            this.is_show_edit = true;
            this.clear_all_errors();
            this.editing_address_index = '';
            this.form_address.title = '';
            this.form_address.receiver = '';
            this.form_address.province_id = '';
            this.form_address.city_id = '';
            this.form_address.district_id = '';
            this.form_address.place = '';
            this.form_address.mobile = '';
            this.form_address.tel = '';
            this.form_address.email = '';
            this.add_title = '增  加';
        },
        // 展示编辑地址弹框时
        show_edit_site(index) {
            this.is_show_edit = true;
            this.clear_all_errors();
            this.editing_address_index = index.toString();``
            // 只获取要编辑的数据，防止修改form_address影响到addresses数据
            this.form_address = JSON.parse(JSON.stringify(this.addresses[index]));
            this.add_title = '修  改';
        },
        // 新增地址
        save_address() {
            this.check_receiver();
            this.check_place();
            this.check_mobile();
            this.check_tel();
            this.check_email();

            if (this.error_receiver || this.error_place || this.error_mobile || this.error_email || !this.form_address.province_id || !this.form_address.city_id || !this.form_address.district_id) {
                alert('信息填写有误！');
            } else {
                // 收货人默认就是收货地址标题
                this.form_address.title = this.form_address.receiver;
                // 注意：0 == '';返回true; 0 === '';返回false;
                if (this.editing_address_index === '') {
                    // 新增地址
                    var url = this.host + '/addresses/create/';
                    axios.post(url, this.form_address, {
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        responseType: 'json'
                    })
                        .then(response => {
                            if (response.data.code == '0') {
                                // location.reload();
                                // 局部刷新界面：展示所有地址信息，将新的地址添加到头部
                                this.addresses.splice(0, 0, response.data.address);
                                this.is_show_edit = false;
                            } else if (response.data.code == '4101') {
                                location.href = '/login/?next=/addresses/';
                            } else if (response.data.code == '4007') {
                                this.error_mobile = true;
                            } else if (response.data.code == '5002') {
                                this.error_tel = true;
                            } else if (response.data.code == '5001') {
                                this.error_email = true;
                            } else { // 4002 4003 5000 (以提示框的形式出现)
                                alert(response.data.errmsg);
                            }
                        })
                        .catch(error => {
                            console.log(error.response);
                        });
                } else {
                    // 修改地址
                    var url = this.host + '/addresses/' + this.addresses[this.editing_address_index].id + '/';
                    axios.put(url, this.form_address, {
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        responseType: 'json'
                    })
                        .then(response => {
                            if (response.data.code == '0') {
                                this.addresses[this.editing_address_index] = response.data.address;
                                this.is_show_edit = false;
                            } else if (response.data.code == '4101') {
                                location.href = '/login/?next=/addresses/';
                            } else if (response.data.code == '4007') {
                                this.error_mobile = true;
                            } else if (response.data.code == '5002') {
                                this.error_tel = true;
                            } else if (response.data.code == '5001') {
                                this.error_email = true;
                            } else { // 4003 5000 (以弹框的形式出现)
                                alert(response.data.errmsg);
                            }
                        })
                        .catch(error => {
                            alert(error.response);
                        })
                }
            }
        },
        // 删除地址
        delete_address(index) {
            var url = this.host + '/addresses/' + this.addresses[index].id + '/';
            axios.delete(url, {
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                responseType: 'json'
            })
                .then(response => {
                    if (response.data.code == '0') {
                        // 删除对应的标签
                        this.addresses.splice(index, 1);
                    } else if (response.data.code == '4101') {
                        location.href = '/login/?next=/addresses/';
                    } else {
                        alert(response.data.errmsg);
                    }
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
        // 设置默认地址
        set_default(index) {
            var url = this.host + '/addresses/' + this.addresses[index].id + '/default/';
            axios.put(url, {}, {
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                responseType: 'json'
            })
                .then(response => {
                    if (response.data.code == '0') {
                        // 设置默认地址标签
                        this.default_address_id = this.addresses[index].id;
                    } else if (response.data.code == '4101') {
                        location.href = '/login/?next=/addresses/';
                    } else {
                        alert(response.data.errmsg);
                    }
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
        // 设置地址title
        show_edit_title(index) {
            this.edit_title_index = index;
        },
        // 取消保存地址title
        cancel_title() {
            this.edit_title_index = '';
            this.input_title = '';
        },
        // 保存地址title
        save_title(index) {
            if (!this.input_title) {
                alert("请填写标题后再保存！");
            } else {
                var url = this.host + '/addresses/' + this.addresses[index].id + '/title/';
                axios.put(url, {
                    title: this.input_title
                }, {
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    responseType: 'json'
                })
                    .then(response => {
                        if (response.data.code == '0') {
                            // 更新地址title
                            this.addresses[index].title = this.input_title;
                            this.cancel_title();
                        } else if (response.data.code == '4101') {
                            location.href = '/login/?next=/addresses/';
                        } else {
                            alert(response.data.errmsg);
                        }
                    })
                    .catch(error => {
                        console.log(error.response);
                    })
            }
        },
    }
});
