var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host: host,
        error_name: false,
        error_password: false,
        error_check_password: false,
        error_phone: false,
        error_image_code: false,
        error_sms_code: false,
        error_allow: false,
        error_name_message: '请输入5-20个字符的用户',
        error_password_message: '请输入8-20位的密码',
        error_password2_message: '两次输入的密码不一致',
        error_phone_message: '请输入正确的手机号码',
        error_image_code_message: '请填写图形验证码',
        error_sms_code_message: '请填写短信验证码',
        error_allow_message: '请勾选用户协议',
        uuid: '',
        image_code_url: '',
        sms_code_tip: '获取短信验证码',
        sending_flag: false,
        username: '',
        password: '',
        password2: '',
        mobile: '',
        image_code: '',
        sms_code: '',
        allow: true
    },
    mounted: function () {
        // 向服务器获取图片验证码
        this.generate_image_code();
    },
    methods: {
        generateUUID: function () {
            var d = new Date().getTime();
            if (window.performance && typeof window.performance.now === "function") {
                d += performance.now(); //use high-precision timer if available
            }
            var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
                var r = (d + Math.random() * 16) % 16 | 0;
                d = Math.floor(d / 16);
                return (c == 'x' ? r : (r & 0x3 | 0x8)).toString(16);
            });
            return uuid;
        },
        // 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
        generate_image_code: function () {
            // 生成一个编号 : 严格一点的使用uuid保证编号唯一， 不是很严谨的情况下，也可以使用时间戳
            this.uuid = this.generateUUID();
            // 设置页面中图片验证码img标签的src属性
            this.image_code_url = this.host + "/image_codes/" + this.uuid + "/";
            console.log(this.image_code_url);
        },
        // 检查用户名
        check_username: function () {
            var re = /^[a-zA-Z0-9_-]{5,20}$/;
            if (re.test(this.username)) {
                this.error_name = false;
            } else {
                this.error_name_message = '请输入5-20个字符的用户名';
                this.error_name = true;
            }
            // 检查重名
            if (this.error_name == false) {
                var url = this.host + '/usernames/' + this.username + '/count/';
                axios.get(url, {
                    responseType: 'json'
                })
                    .then(response => {
                        if (response.data.count > 0) {
                            this.error_name_message = '用户名已存在';
                            this.error_name = true;
                        } else {
                            this.error_name = false;
                        }
                    })
                    .catch(error => {
                        console.log(error.response);


                    })
            }
        },
        // 检查密码
        check_pwd: function () {
            var re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.password)) {
                this.error_password = false;
            } else {
                this.error_password = true;
            }
        },
        // 确认密码
        check_cpwd: function () {
            if (this.password != this.password2) {
                this.error_check_password = true;
            } else {
                this.error_check_password = false;
            }
        },
        // 检查手机号
        check_phone: function () {
            var re = /^1[345789]\d{9}$/;
            if (re.test(this.mobile)) {
                this.error_phone = false;
            } else {
                this.error_phone_message = '您输入的手机号格式不正确';
                this.error_phone = true;
            }
            if (this.error_phone == false) {
                var url = this.host + '/mobiles/' + this.mobile + '/count/';
                axios.get(url, {
                    responseType: 'json'
                })
                    .then(response => {
                        if (response.data.count > 0) {
                            this.error_phone_message = '手机号已存在';
                            this.error_phone = true;
                        } else {
                            this.error_phone = false;
                        }
                    })
                    .catch(error => {
                        console.log(error.response);
                    })
            }
        },
        // 检查图片验证码
        check_image_code: function () {
            if (!this.image_code) {
                this.error_image_code_message = '请填写图片验证码';
                this.error_image_code = true;
            } else {
                this.error_image_code = false;
            }

        },
        // 检查短信验证码
        check_sms_code: function () {
            if (!this.sms_code) {
                this.error_sms_code_message = '请填写短信验证码';
                this.error_sms_code = true;
            } else {
                this.error_sms_code = false;
            }
        },
        // 检查是否勾选协议
        check_allow: function () {
            if (!this.allow) {
                this.error_allow = true;
            } else {
                this.error_allow = false;
            }
        },
        click_allow: function () {
            this.allow = !this.allow
            this.check_allow()
        },
        // 发送手机短信验证码
        send_sms_code: function () {
            if (this.sending_flag == true) {
                return;
            }
            this.sending_flag = true;

            // 校验参数，保证输入框有数据填写
            this.check_phone();
            this.check_image_code();

            if (this.error_phone == true || this.error_image_code == true) {
                this.sending_flag = false;
                return;
            }

            // 向后端接口发送请求，让后端发送短信验证码
            var url = this.host + '/sms_codes/' + this.mobile + '/?image_code=' + this.image_code + '&uuid=' + this.uuid;
            axios.get(url, {
                responseType: 'json'
            })
                .then(response => {
                    // 表示后端发送短信成功
                    if (response.data.code == '0') {
                        // 倒计时60秒，60秒后允许用户再次点击发送短信验证码的按钮
                        var num = 60;
                        // 设置一个计时器
                        var t = setInterval(() => {
                            if (num == 1) {
                                // 如果计时器到最后, 清除计时器对象
                                clearInterval(t);
                                // 将点击获取验证码的按钮展示的文本回复成原始文本
                                this.sms_code_tip = '获取短信验证码';
                                // 将点击按钮的onclick事件函数恢复回去
                                this.sending_flag = false;
                            } else {
                                num -= 1;
                                // 展示倒计时信息
                                this.sms_code_tip = num + '秒';
                            }
                        }, 1000, 60)
                    } else {
                        if (response.data.code == '4001') {
                            this.error_image_code_message = response.data.errmsg;
                            this.error_image_code = true;
                        } else { // 4002
                            this.error_sms_code_message = response.data.errmsg;
                            this.error_sms_code = true;
                        }
                        this.generate_image_code();
                        this.sending_flag = false;
                    }
                })
                .catch(error => {
                    console.log(error.response);
                    this.sending_flag = false;
                })
        },
        // 表单提交
        on_submit() {
            this.check_username();
            this.check_pwd();
            this.check_cpwd();
            this.check_phone();
            this.check_sms_code();
            this.check_allow();

            if (this.error_name == true || this.error_password == true || this.error_check_password == true
                || this.error_phone == true || this.error_sms_code == true || this.error_allow == true) {
                // 不满足注册条件：禁用表单
                window.event.returnValue = false;
            }

            // var url = this.host + '/register/';
            // axios.post(url, {
            //     username: this.username,
            //     password: this.password,
            //     password2: this.password2,
            //     mobile: this.mobile,
            //     // 'image_code':this.image_code,
            //     sms_code: this.sms_code,
            //     allow: this.allow
            // }, {
            //     responseType: 'json'
            // })
            //     .then(response => {
            //     })
            //     .catch(error => {
            //     });
        }
    }
});


// vue注册
// on_submit: function(){
// 			this.check_username();
// 			this.check_pwd();
// 			this.check_cpwd();
// 			this.check_phone();
// 			this.check_sms_code();
// 			this.check_allow();
//
// 			if(this.error_name == false && this.error_password == false && this.error_check_password == false
// 				&& this.error_phone == false && this.error_sms_code == false && this.error_allow == false) {
//
// 				var url = this.host + '/register/';
// 				axios.post(url, {
// 						username: this.username,
// 						password: this.password,
// 						password2: this.password2,
// 						mobile: this.mobile,
// 						sms_code: this.sms_code,
// 						allow: this.allow.toString()
// 					},{
// 						headers: {
// 							'X-CSRFToken':getCookie('csrftoken')
// 						},
// 						responseType: 'json',
// 					})
// 					.then(response => {
// 						// 注册成功
// 						if (response.data.code == '0') {
// 							location.href = '/';
// 						} else {
// 							if (response.data.code == '4003') {
// 								alert(response.data.errmsg);
// 							} else if (response.data.code == '4004') {
// 								this.error_name_message = response.data.errmsg;
// 								this.error_name = true;
// 							} else if (response.data.code == '4005') {
// 								this.error_password = true;
// 							} else if (response.data.code == '4006') {
// 								this.error_check_password = true;
// 							} else if (response.data.code == '4007') {
// 								this.error_phone_message = response.data.errmsg;
// 								this.error_phone = true;
// 							} else if (response.data.code == '4008') {
// 								this.error_sms_code_message = response.data.errmsg;
// 								this.error_sms_code = true;
// 							} else if (response.data.code == '4009') {
// 								this.error_allow = true;
// 							} else { // 5000
// 								alert(response.data.errmsg);
// 							}
// 						}
// 					})
// 					.catch(error => {
// 						console.log(error.response);
// 					})
// 			}
// 		}


// var error_name = true;
// var error_password = true;
// var error_check_password = true;
// var error_phone = true;
// var error_pic_code = true;
// var error_msg_code = true;
// var error_allow = false;
//
// $(function(){
// 	$('#user_name').blur(function() {
// 		check_user_name();
// 	});
//
// 	$('#pwd').blur(function() {
// 		check_pwd();
// 	});
//
// 	$('#cpwd').blur(function() {
// 		check_cpwd();
// 	});
//
// 	$('#phone').blur(function() {
// 		check_phone();
// 	});
//
//     $('#pic_code').blur(function() {
// 		check_pic_code();
//     });
//
// 	$('#msg_code').blur(function() {
// 		check_msg_code();
// 	});
//
// 	// 校验用户名:5-20位
// 	function check_user_name(){
// 		var re = /^[a-zA-Z0-9_-]{5,20}$/;
// 		var username = $('#user_name').val();
// 		if(re.test(username)) {
// 			$('#user_name').next().empty();
// 			error_name = false;
//
// 			// 判断用户名是否重复
// 			username_repeat();
// 		} else {
// 			$('#user_name').next().html('请输入5-20个字符的用户名');
// 			error_name = true;
// 		}
// 	}
//
// 	// 校验密码：是否是8-20位字符（由数字或者字母组成）
// 	function check_pwd(){
// 		var re = /^[0-9A-Za-z]{8,20}$/;
// 		var pwd = $('#pwd').val();
// 		if(re.test(pwd)) {
// 			$('#pwd').next().empty();
// 			error_password = false;
// 		} else {
// 			$('#pwd').next().html('请输入8-20位的密码');
// 			error_password = true;
// 		}
// 	}
//
// 	// 校验确认密码
// 	function check_cpwd(){
// 		var pass = $('#pwd').val();
// 		var cpass = $('#cpwd').val();
//
// 		if(pass!=cpass) {
// 			$('#cpwd').next().html('两次输入的密码不一致');
// 			error_check_password = true;
// 		} else {
// 			$('#cpwd').next().empty();
// 			error_check_password = false;
// 		}
// 	}
//
// 	// 校验手机号
// 	function check_phone(){
// 		var re = /^1[3-9]\d{9}$/;
// 		var mobile = $('#phone').val();
//
// 		if(re.test(mobile)) {
// 			$('#phone').next().empty();
// 			error_phone = false;
//
// 			// 判断用户名是否重复
// 			mobile_repeat();
// 		} else {
// 			$('#phone').next().html('请输入正确的手机号码');
// 			error_phone = true;
// 		}
// 	}
//
// 	// 校验图形验证码
// 	function check_pic_code(){
// 		var len = $('#pic_code').val().length;
// 		if(len!=4) {
// 			$('#pic_code').next().next().html('请填写图形验证码');
// 			error_pic_code = true;
// 		} else {
// 			$('#pic_code').next().next().empty();
// 			error_pic_code = false;
// 		}
// 	}
//
//     // 校验短信验证码
// 	function check_msg_code(){
// 		// var msg_code = $('#msg_code').val();
// 		var len = $('#msg_code').val().length;
// 		if(len!=6) {
// 			$('#msg_code').next().next().html('请填写短信验证码');
// 			error_msg_code = true;
// 		} else {
// 			$('#msg_code').next().next().empty();
// 			error_msg_code = false;
// 		}
// 	}
//
// 	// 点击勾选协议
//     $('#allow').click(function() {
// 		if($(this).is(':checked')) {
// 			$(this).siblings('span').empty();
// 			error_allow = false;
// 		} else {
// 			$(this).siblings('span').html('请勾选用户协议');
// 			error_allow = true;
// 		}
// 	});
//
//     // 点击注册标签
//     $('.register_form').submit(function() {
//
// 		// check_user_name();
// 		// check_pwd();
// 		// check_cpwd();
// 		// check_phone();
// 		// check_pic_code();
// 		// check_msg_code();
//
// 		if(error_name == false && error_password == false && error_check_password == false && error_phone == false && error_pic_code == false && error_msg_code == false && error_allow == false)
// 		{
// 		    return true
// 		} else {
// 			alert('请输入完整注册信息');
// 			return false;
// 		}
// 	});
//
//     // 生成图片验证码
// 	generateImageCode();
// });
//
// var imageCodeId = "";
//
// // 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
// function generateImageCode() {
//     // 获取uuid
//     imageCodeId = generateUUID();
//     // 生成获取图片验证码的url
//     var url = '/image_codes/' + imageCodeId + '/';
//     // 将url设置到img标签的src数据
//     $('.pic_code').attr('src', url);
// }
//
// // 点击发送短信验证码
// function sendSMSCode() {
//     // 移除点击事件，避免重复点击
//     $(".get_msg_code").removeAttr("onclick");
//
//     // 校验参数，保证输入框有数据填写
//     var mobile = $("#phone").val();
//     var image_code = $('#pic_code').val();
//
//     if (error_phone==true || error_pic_code==true) {
//     	$(".get_msg_code").attr("onclick", "sendSMSCode();");
//     	return;
// 	}
//
//     // 发送短信验证码
//     var url = '/sms_codes/' + mobile + '/?image_code=' + image_code + '&image_code_id=' + imageCodeId;
//     $.get(url, function (response) {
//         if (response.code == "0") {
//             // 发送成功后，进行倒计时
//             var num = 60;
//             var t = setInterval(function () {
//                 if (num == 0) {
//                     // 倒计时结束,清除定时器
//                     clearInterval(t); 
//                     // 倒计时结束,重置内容
//                     $(".get_msg_code").html('获取短信验证码');
//                     // $('#msg_code').next().next().html();
//                     // 倒计时结束，重新添加点击事件
//                     $(".get_msg_code").attr("onclick", "sendSMSCode();");
//                     generateImageCode();
//                 } else {
//                     // 正在倒计时，显示秒数
//                     $(".get_msg_code").html(num + '秒');
//                 }
//                 // 每一秒减一
//                 num -= 1;
//             }, 1000);
//         } else if (response.code == '4201') {
//         	// 展示频繁发送短信的错误提示信息
// 			$('#msg_code').next().next().html("发送短信过于频繁");
// 			// 2秒钟后消失
// 			$('#msg_code').next().next().show().delay(2000).fadeOut();
// 			// 重新添加点击事件
//             $(".get_msg_code").attr("onclick", "sendSMSCode();");
// 		} else {
//             alert(response.errmsg);
//             // 重新添加点击事件
//             $(".get_msg_code").attr("onclick", "sendSMSCode();");
//             generateImageCode();
//         }
//     });
// }
//
//
// // 判断用户名是否重复
// function username_repeat() {
// 	var username = $('#user_name').val();
// 	var url = '/usernames/' + username + '/count/';
// 	$.get(url, function (response) {
// 		if (response.count == 1) {
// 			$('#user_name').next().html('用户名已存在');
// 			error_name = true;
// 		} else {
// 			console.log(response);
// 		}
// 	});
// }
//
//
// // 判断用户名是否重复
// function mobile_repeat() {
// 	var mobile = $('#phone').val();
// 	var url = '/mobiles/' + mobile + '/count/';
// 	$.get(url, function (response) {
// 		if (response.count == 1) {
// 			$('#phone').next().html('手机号已存在');
// 			error_phone = true;
// 		} else {
// 			console.log(response);
// 		}
// 	});
// }
//
//
// function generateUUID() {
//     var d = new Date().getTime();
//     if(window.performance && typeof window.performance.now === "function"){
//         d += performance.now(); //use high-precision timer if available
//     }
//     var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
//         var r = (d + Math.random()*16)%16 | 0;
//         d = Math.floor(d/16);
//         return (c=='x' ? r : (r&0x3|0x8)).toString(16);
//     });
//     return uuid;
// }