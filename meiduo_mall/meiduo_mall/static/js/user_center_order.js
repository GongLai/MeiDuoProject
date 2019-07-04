var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host: host,
    },
    mounted(){

    },
    methods: {
        oper_btn_click(order_id, status){
            if (status == '1') {
                // 待支付
                var url = this.host + '/payment/' + order_id + '/';
                axios.get(url, {
                    responseType: 'json'
                })
                    .then(response => {
                        if (response.data.code == '0') {
                            location.href = response.data.alipay_url;
                        } else {
                            console.log(response.data);
                            alert(response.data.errmsg);
                        }
                    })
                    .catch(error => {
                        console.log(error.response);
                    });
            } else if (status == '4') {
                // 待评价
                location.href = '/orders/comment/?order_id=' + order_id;
            } else {
                // 其他：待收货。。。
                location.href = '/';
            }
        },
    }
});








// $(function () {
//
// });
//
//
// $('.oper_btn').click(function () {
//     var order_id = $(this).attr('order_id');
//     var status = $(this).attr('order_status');
//
//     if (status == '1') {
//         // 待支付
//         var url = '/payment/' + order_id + '/';
//         $.get(url, function (response) {
//             if (response.code == '0') {
//                 location.href = response.alipay_url;
//             } else {
//                 console.log(response);
//                 alert(response.errmsg);
//             }
//         });
//     } else if (status == '4') {
//         // 待评价
//         location.href = '/orders/comment/?order_id=' + order_id;
//     } else {
//         // 其他：待收货。。。
//         location.href = '/index/'
//     }
// });