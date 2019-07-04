var vm = new Vue({
    el: '#app',
	// 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
    },
    mounted(){
    },
    methods: {
        // 发起支付
        order_payment(){
            var order_id = get_query_string('order_id');
            var url = '/payment/' + order_id + '/';
            axios.get(url, {
                    responseType: 'json'
                })
                .then(response => {
                    if (response.data.code == '0') {
                        // 跳转到支付宝
                        location.href = response.data.alipay_url;
                    } else if (response.data.code == '4101') {
                        location.href = '/login/?next=/orders/info/1/';
                    } else {
                        console.log(response.data);
                        alert(response.data.errmsg);
                    }
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
    }
});











// $(function () {
//
// });
//
//
// $('.payment').click(function () {
//     var order_id = get_query_string('order_id');
//     var url = '/payment/' + order_id + '/';
//     $.get(url, function (response) {
//         if (response.code == '0') {
//             location.href = response.alipay_url;
//         } else if (response.code == '4101') {
//             location.href = '/login/?next=/orders/info/1/';
//         } else {
//             console.log(response);
//             alert(response.errmsg);
//         }
//     });
// });
