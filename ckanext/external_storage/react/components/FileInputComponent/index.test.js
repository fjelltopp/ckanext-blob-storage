import { render, act, fireEvent, screen } from '@testing-library/react';
import App from './src/app';
import axios from 'axios'
import * as giftless from "giftless-client";

jest.mock('axios');
giftless.Client = jest.fn(() => ({
  default: jest.fn(),
  upload: jest.fn()
}));

//afterEach(() => screen.debug())

beforeEach(async () => {
  await act(async () => {

    // arrange
    const mockedAppProps = {
      lfsServer: 'mockedLfsServer',
      orgId: 'mockedOrgId',
      datasetId: 'mockedDatasetId',
      existingResourceData: {
        urlType: null,
        url: null,
        sha256: null,
        name: null,
        fileName: null,
        size: null,
      }
    };
    const mockedAxiosPost = axios.post.mockImplementation(() =>
      Promise.resolve({
        data: { result: { token: 'MockedToken' } }
      })
    );

    // act
    const { getByTestId } = render(<App {...mockedAppProps} />);

    // wait for intial useEffect to run
    await new Promise(resolve => setTimeout(resolve, 20));
    expect(mockedAxiosPost).toHaveBeenCalled();

    // assert
    expect(getByTestId('FileUploaderButton')).toBeInTheDocument();
    expect(getByTestId('UrlUploaderButton')).toBeInTheDocument();

  })
})

describe('url upload', () => {

  test('correct inputs are displayed', async () => {

    // act
    fireEvent.click(screen.getByTestId('UrlUploaderButton'));
    expect(screen.getByTestId('UrlUploaderComponent')).toBeInTheDocument();
    expect(screen.getByTestId('UrlInputField')).toBeInTheDocument();

    // assert
    expect(screen.getByTestId('url_type')).toHaveValue('')
    expect(screen.getByTestId('lfs_prefix')).toHaveValue('')
    expect(screen.getByTestId('sha256')).toHaveValue('')
    expect(screen.getByTestId('size')).toHaveValue('')

  });

});

describe('file upload', () => {

  const uploadFileToElement = async elementTestId => {
    // arrange
    const component = screen.getByTestId(elementTestId);

    // act
    const file = new File(['file'], 'data.json');
    Object.defineProperty(component, 'files', { value: [file] });
    fireEvent.drop(component);

    // assert
    await screen.findByText('data.json')
  }

  test('file upload using the <input type="file" />', async () => {
    await uploadFileToElement('FileUploaderInput');
  });

  test('file upload using drag and drop', async () => {
    await uploadFileToElement('FileUploaderComponent');
  });

  test('correct inputs are displayed', async () => {

    // arrange & act
    await uploadFileToElement('FileUploaderInput');

    // assert
    expect(screen.getByTestId('url_type')).toHaveValue('upload')
    expect(screen.getByTestId('lfs_prefix')).toHaveValue('mockedOrgId/mockedDatasetId')
    expect(screen.getByTestId('sha256')).toHaveValue('mockedSha256')
    expect(screen.getByTestId('size')).toHaveValue('1337')
  });

});
