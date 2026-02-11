import React from 'react';
import { Form, InputNumber, Button, Card, Typography, Row, Col, Divider, Select } from 'antd';
import { DollarOutlined, SolutionOutlined, UserOutlined, ClockCircleOutlined, HomeOutlined, TeamOutlined, SafetyCertificateOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

const CreditForm = ({ onSubmit, isLoading }) => {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    // Mapping dữ liệu chuẩn form backend
    const formattedValues = {
      ...values,
      DAYS_BIRTH: -Math.abs(values.age * 365), 
      DAYS_EMPLOYED: -Math.abs(values.years_employed * 365),
      // Giữ nguyên các giá trị Select (Housing, Family...) vì Backend đã xử lý string
    };
    onSubmit(formattedValues);
  };

  return (
    <Card 
      style={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 12, border: 'none', boxShadow: 'none' }}
      bodyStyle={{ flex: 1, padding: '0 10px' }}
    >
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0, color: '#1f1f1f' }}>Hồ sơ vay vốn</Title>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        size="large"
        initialValues={{
          AMT_INCOME_TOTAL: 500000000, 
          AMT_CREDIT: 1000000000,      
          AMT_ANNUITY: 25000000,
          age: 30,
          years_employed: 5,
          NAME_HOUSING_TYPE: "House / apartment",
          NAME_FAMILY_STATUS: "Married",
          EXT_SOURCE_2: 0.7 // Mặc định Lịch sử tốt
        }}
      >
        <Title level={5} style={{ color: '#B01E23' }}><DollarOutlined /> Tài chính</Title>
        <Row gutter={16}>
          <Col span={24}>
            <Form.Item label="Tổng thu nhập (năm)" name="AMT_INCOME_TOTAL" rules={[{ required: true }]}>
               <InputNumber style={{ width: '100%' }} formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} parser={value => value.replace(/\$\s?|(,*)/g, '')} addonAfter="VND" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="Số tiền vay" name="AMT_CREDIT" rules={[{ required: true }]}>
               <InputNumber style={{ width: '100%' }} formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} parser={value => value.replace(/\$\s?|(,*)/g, '')} />
            </Form.Item>
          </Col>
          <Col span={12}>
             <Form.Item label="Trả hàng tháng" name="AMT_ANNUITY" rules={[{ required: true }]}>
               <InputNumber style={{ width: '100%' }} formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} parser={value => value.replace(/\$\s?|(,*)/g, '')} />
            </Form.Item>
          </Col>
        </Row>

        <Divider style={{ margin: '12px 0' }} />

        <Title level={5} style={{ color: '#B01E23' }}><SolutionOutlined /> Nhân khẩu & Hành vi</Title>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="Tuổi" name="age" rules={[{ required: true }]}>
              <InputNumber style={{ width: '100%' }} min={18} max={70} prefix={<UserOutlined />} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="Thâm niên (năm)" name="years_employed">
              <InputNumber style={{ width: '100%' }} min={0} max={50} prefix={<ClockCircleOutlined />} />
            </Form.Item>
          </Col>
          
          {/* CÁC TRƯỜNG MỚI QUAN TRỌNG */}
          <Col span={12}>
            <Form.Item label="Nhà ở" name="NAME_HOUSING_TYPE">
              <Select>
                <Option value="House / apartment"><HomeOutlined /> Nhà riêng</Option>
                <Option value="Rented apartment"><HomeOutlined /> Nhà thuê</Option>
                <Option value="With parents">Ở cùng bố mẹ</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="Gia đình" name="NAME_FAMILY_STATUS">
              <Select>
                 <Option value="Married"><TeamOutlined /> Đã kết hôn</Option>
                 <Option value="Single / not married"><UserOutlined /> Độc thân</Option>
                 <Option value="Civil marriage">Sống chung</Option>
              </Select>
            </Form.Item>
          </Col>
          
          <Col span={24}>
             <Form.Item 
                label={<span style={{color: '#B01E23', fontWeight: 'bold'}}>Lịch sử Tín dụng</span>} 
                name="EXT_SOURCE_2"
                tooltip="Mô phỏng dữ liệu từ trung tâm tín dụng quốc gia"
             >
               <Select size="large" style={{ border: '1px solid #B01E23', borderRadius: 6 }}>
                 <Option value={0.85}> Rất Tốt (Chưa từng trễ hạn)</Option>
                 <Option value={0.65}> Khá (Thỉnh thoảng trễ nhẹ)</Option>
                 <Option value={0.45}> Trung bình (Có nợ chú ý)</Option>
                 <Option value={0.20}> Nợ Xấu (Đang có nợ quá hạn)</Option>
               </Select>
             </Form.Item>
          </Col>
        </Row>

        <Form.Item style={{ marginTop: 20 }}>
          <Button 
            type="primary" htmlType="submit" size="large" block loading={isLoading}
            style={{ height: 50, fontSize: 18, fontWeight: 700, background: '#B01E23', borderColor: '#B01E23' }}
          >
            PHÂN TÍCH RỦI RO
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default CreditForm;